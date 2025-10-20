"""
Serviço para gerenciar monetização de posts e transações.
Implementa lógica de pagamentos, assinaturas e controle de acesso a conteúdo pago.
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Tuple, Any
import uuid
from decimal import Decimal

try:
    # Import opcional; cliente será obtido apenas se app Firebase estiver inicializado
    from firebase_admin import firestore
except Exception:
    firestore = None

# Removida importação circular - UserService será importado dinamicamente quando necessário

logger = logging.getLogger(__name__)

# Integração opcional com Stripe
try:
    from services.payments.stripe_service import StripeService
except Exception:
    StripeService = None

class MonetizationService:
    """Serviço para gerenciar monetização."""
    
    def __init__(self, firebase_service=None):
        """Inicializa o serviço de monetização.
        
        Se um `firebase_service` for fornecido e possuir `db` válido, usa-o.
        Caso contrário, tenta obter um cliente Firestore apenas se o app Firebase
        estiver inicializado; se não estiver, mantém `db=None` e opera em modo simulado
        quando os métodos forem chamados (sem quebrar a inicialização do bot).
        """
        self.db = None
        self.simulation_mode = True

        # Tentar usar o db do FirebaseService, se disponível
        if firebase_service and getattr(firebase_service, 'db', None):
            self.db = firebase_service.db
            self.simulation_mode = False
        else:
            try:
                import firebase_admin
                if firestore and getattr(firebase_admin, '_apps', None):
                    if firebase_admin._apps:
                        self.db = firestore.client()
                        self.simulation_mode = False
                    else:
                        logging.warning("Firebase app não inicializado; MonetizationService em modo simulado")
                else:
                    logging.warning("Firestore indisponível ou Firebase não inicializado; modo simulado ativo")
            except Exception as e:
                logging.warning(f"MonetizationService não pôde obter Firestore: {e}. Usando modo simulado")

        # UserService será importado dinamicamente quando necessário para evitar importação circular
        
        # Coleções do Firestore
        self.transactions_collection = 'transactions'
        self.subscriptions_collection = 'subscriptions'
        self.payments_collection = 'payments'
        self.wallet_collection = 'wallets'
        self.earnings_collection = 'earnings'
    
    async def create_payment_intent(self, user_id: int, post_id: str, amount: float, currency: str = 'BRL') -> Optional[Dict]:
        """
        Cria uma intenção de pagamento para acessar conteúdo pago.
        
        Args:
            user_id: ID do usuário que vai pagar
            post_id: ID do post a ser acessado
            amount: Valor do pagamento
            currency: Moeda (padrão BRL)
            
        Returns:
            Dict: Dados da intenção de pagamento ou None se houve erro
        """
        try:
            # Verificar se o usuário já tem acesso ao post
            if await self.has_access_to_post(user_id, post_id):
                logger.warning(f"Usuário {user_id} já tem acesso ao post {post_id}")
                return None
            
            # Gerar ID único para a transação
            transaction_id = str(uuid.uuid4())
            
            # Criar documento de transação
            transaction_data = {
                'id': transaction_id,
                'user_id': user_id,
                'post_id': post_id,
                'amount': amount,
                'currency': currency,
                'status': 'pending',
                'type': 'post_access',
                'created_at': datetime.now(),
                'updated_at': datetime.now(),
                
                # Metadados para integração com gateway de pagamento
                'payment_method': None,
                'payment_gateway': 'stripe',  # ou outro gateway
                'gateway_transaction_id': None,
                'gateway_status': None,
                
                # Dados para split de pagamento
                'platform_fee_percentage': 10.0,  # Taxa da plataforma
                'creator_amount': amount * 0.9,
                'platform_amount': amount * 0.1
            }
            
            # Salvar no Firestore
            transaction_ref = self.db.collection(self.transactions_collection).document(transaction_id)
            transaction_ref.set(transaction_data)
            
            logger.info(f"Intenção de pagamento criada: {transaction_id}")

            # Integrar com Stripe para criar PaymentIntent, se habilitado
            client_secret = None
            try:
                if StripeService:
                    stripe_service = StripeService()
                    if getattr(stripe_service, 'enabled', False):
                        intent_data = stripe_service.create_payment_intent(
                            transaction_id=transaction_id,
                            amount=amount,
                            currency=currency,
                            metadata={"user_id": user_id, "post_id": post_id, "type": "post_access"},
                            platform_fee_percentage=transaction_data['platform_fee_percentage'],
                            destination_account=None  # Opcional: conta conectada do criador
                        )
                        if intent_data:
                            client_secret = intent_data.get('client_secret')
                            # Atualizar transação com dados do gateway
                            transaction_ref.update({
                                'payment_method': 'stripe',
                                'gateway_transaction_id': intent_data.get('payment_intent_id'),
                                'gateway_status': intent_data.get('status'),
                                'updated_at': datetime.now()
                            })
                            logger.info(f"PaymentIntent criado no Stripe para {transaction_id}")
                    else:
                        logger.info("StripeService não habilitado; mantendo intenção pendente localmente")
                else:
                    logger.info("StripeService indisponível; libraria não carregada ou arquivo ausente")
            except Exception as e:
                logger.error(f"Falha na criação de PaymentIntent Stripe: {e}")
            
            # Registrar atividade
            await self._log_user_activity(user_id, 'payment_intent_created', {
                'transaction_id': transaction_id,
                'post_id': post_id,
                'amount': amount
            })
            
            return {
                'transaction_id': transaction_id,
                'amount': amount,
                'currency': currency,
                'status': 'pending',
                'client_secret': client_secret
            }
            
        except Exception as e:
            logger.error(f"Erro ao criar intenção de pagamento: {e}")
            return None
    
    async def process_payment(self, transaction_id: str, payment_data: Dict) -> bool:
        """
        Processa um pagamento confirmado.
        
        Args:
            transaction_id: ID da transação
            payment_data: Dados do pagamento do gateway
            
        Returns:
            bool: True se o pagamento foi processado com sucesso
        """
        try:
            # Obter dados da transação
            transaction_ref = self.db.collection(self.transactions_collection).document(transaction_id)
            transaction_doc = transaction_ref.get()
            
            if not transaction_doc.exists:
                logger.error(f"Transação não encontrada: {transaction_id}")
                return False
            
            transaction_data = transaction_doc.to_dict()
            
            if transaction_data['status'] != 'pending':
                logger.warning(f"Transação {transaction_id} não está pendente: {transaction_data['status']}")
                return False
            
            # Usar transação do Firestore para garantir consistência
            db_transaction = self.db.transaction()
            
            @firestore.transactional
            def process_payment_transaction(db_transaction):
                # Atualizar status da transação
                db_transaction.update(transaction_ref, {
                    'status': 'completed',
                    'completed_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'payment_method': payment_data.get('payment_method'),
                    'gateway_transaction_id': payment_data.get('gateway_transaction_id'),
                    'gateway_status': payment_data.get('gateway_status')
                })
                
                # Criar registro de acesso ao post
                access_data = {
                    'user_id': transaction_data['user_id'],
                    'post_id': transaction_data['post_id'],
                    'transaction_id': transaction_id,
                    'granted_at': datetime.now(),
                    'expires_at': None,  # Acesso permanente por enquanto
                    'status': 'active'
                }
                
                access_ref = self.db.collection('post_access').document()
                db_transaction.set(access_ref, access_data)
                
                # Registrar ganhos para o criador
                earnings_data = {
                    'creator_id': None,  # Será preenchido depois
                    'post_id': transaction_data['post_id'],
                    'transaction_id': transaction_id,
                    'amount': transaction_data['creator_amount'],
                    'currency': transaction_data['currency'],
                    'earned_at': datetime.now(),
                    'status': 'pending_withdrawal'
                }
                
                earnings_ref = self.db.collection(self.earnings_collection).document()
                db_transaction.set(earnings_ref, earnings_data)
                
                return access_ref.id, earnings_ref.id
            
            access_id, earnings_id = process_payment_transaction(db_transaction)
            
            logger.info(f"Pagamento processado com sucesso: {transaction_id}")
            
            # Registrar atividades
            await self._log_user_activity(transaction_data['user_id'], 'payment_completed', {
                'transaction_id': transaction_id,
                'post_id': transaction_data['post_id'],
                'amount': transaction_data['amount'],
                'access_id': access_id
            })
            
            # Notificar o criador sobre o ganho
            await self._notify_creator_earnings(transaction_data['post_id'], earnings_id)
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao processar pagamento {transaction_id}: {e}")
            return False
    
    async def has_access_to_post(self, user_id: int, post_id: str) -> bool:
        """
        Verifica se o usuário tem acesso a um post pago.
        
        Args:
            user_id: ID do usuário
            post_id: ID do post
            
        Returns:
            bool: True se tem acesso
        """
        try:
            # Verificar se é o próprio criador do post
            from services.post_service import PostService
            post_service = PostService()
            post = await post_service.get_post(post_id)
            
            if post and post.get('creator_id') == user_id:
                return True
            
            # Verificar se o post é gratuito
            if post and not post.get('monetization', {}).get('enabled', False):
                return True
            
            # Verificar se tem acesso pago
            access_query = self.db.collection('post_access')\
                .where('user_id', '==', user_id)\
                .where('post_id', '==', post_id)\
                .where('status', '==', 'active')\
                .limit(1)
            
            access_docs = access_query.get()
            
            if not access_docs:
                return False
            
            # Verificar se o acesso não expirou
            access_data = access_docs[0].to_dict()
            expires_at = access_data.get('expires_at')
            
            if expires_at and expires_at < datetime.now():
                # Marcar como expirado
                access_docs[0].reference.update({
                    'status': 'expired',
                    'updated_at': datetime.now()
                })
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao verificar acesso ao post {post_id} para usuário {user_id}: {e}")
            return False

    def is_premium_user(self, user_data: Dict[str, Any]) -> bool:
        """Verifica se usuário é premium.
        
        Args:
            user_data: Dados do usuário
            
        Returns:
            True se for premium
        """
        if not user_data:
            return False
        
        plan_type = user_data.get('plan_type', 'free')
        return plan_type in ['premium', 'diamond']
    
    async def get_user_transactions(self, user_id: int, limit: int = 50) -> List[Dict]:
        """
        Obtém transações de um usuário.
        
        Args:
            user_id: ID do usuário
            limit: Limite de transações a retornar
            
        Returns:
            List[Dict]: Lista de transações
        """
        try:
            transactions_query = self.db.collection(self.transactions_collection)\
                .where('user_id', '==', user_id)\
                .order_by('created_at', direction=firestore.Query.DESCENDING)\
                .limit(limit)
            
            transactions = transactions_query.get()
            
            result = []
            for transaction_doc in transactions:
                transaction_data = transaction_doc.to_dict()
                transaction_data['id'] = transaction_doc.id
                
                # Enriquecer com dados do post
                post_id = transaction_data.get('post_id')
                if post_id:
                    from services.post_service import PostService
                    post_service = PostService()
                    post = await post_service.get_post(post_id)
                    if post:
                        transaction_data['post'] = {
                            'id': post_id,
                            'title': post.get('title', 'Post não encontrado'),
                            'type': post.get('type', 'unknown')
                        }
                
                result.append(transaction_data)
            
            logger.info(f"Obtidas {len(result)} transações para usuário {user_id}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao obter transações do usuário {user_id}: {e}")
            return []
    
    async def get_creator_earnings(self, creator_id: int, period_days: int = 30) -> Dict:
        """
        Obtém ganhos de um criador.
        
        Args:
            creator_id: ID do criador
            period_days: Período em dias para calcular ganhos
            
        Returns:
            Dict: Dados de ganhos do criador
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=period_days)
            
            # Buscar ganhos no período
            earnings_query = self.db.collection(self.earnings_collection)\
                .where('creator_id', '==', creator_id)\
                .where('earned_at', '>=', cutoff_date)
            
            earnings = earnings_query.get()
            
            total_earnings = 0.0
            pending_withdrawal = 0.0
            completed_withdrawals = 0.0
            transactions_count = 0
            
            earnings_by_status = {
                'pending_withdrawal': 0.0,
                'withdrawn': 0.0,
                'processing': 0.0
            }
            
            for earning_doc in earnings:
                earning_data = earning_doc.to_dict()
                amount = earning_data.get('amount', 0.0)
                status = earning_data.get('status', 'pending_withdrawal')
                
                total_earnings += amount
                transactions_count += 1
                
                if status in earnings_by_status:
                    earnings_by_status[status] += amount
                
                if status == 'pending_withdrawal':
                    pending_withdrawal += amount
                elif status == 'withdrawn':
                    completed_withdrawals += amount
            
            # Calcular ganhos totais (histórico)
            all_earnings_query = self.db.collection(self.earnings_collection)\
                .where('creator_id', '==', creator_id)
            
            all_earnings = all_earnings_query.get()
            total_lifetime_earnings = sum(
                doc.to_dict().get('amount', 0.0) for doc in all_earnings
            )
            
            result = {
                'creator_id': creator_id,
                'period_days': period_days,
                'total_earnings_period': total_earnings,
                'total_lifetime_earnings': total_lifetime_earnings,
                'pending_withdrawal': pending_withdrawal,
                'completed_withdrawals': completed_withdrawals,
                'transactions_count': transactions_count,
                'earnings_by_status': earnings_by_status,
                'average_per_transaction': total_earnings / max(transactions_count, 1)
            }
            
            logger.info(f"Ganhos calculados para criador {creator_id}: R$ {total_earnings:.2f}")
            return result
            
        except Exception as e:
            logger.error(f"Erro ao obter ganhos do criador {creator_id}: {e}")
            return {}
    
    async def request_withdrawal(self, creator_id: int, amount: float, payment_info: Dict) -> Optional[str]:
        """
        Solicita saque de ganhos.
        
        Args:
            creator_id: ID do criador
            amount: Valor a ser sacado
            payment_info: Informações de pagamento (PIX, conta bancária, etc.)
            
        Returns:
            str: ID da solicitação de saque ou None se houve erro
        """
        try:
            # Verificar saldo disponível
            earnings_data = await self.get_creator_earnings(creator_id, period_days=365)
            available_balance = earnings_data.get('pending_withdrawal', 0.0)
            
            if amount > available_balance:
                logger.warning(f"Saldo insuficiente para saque. Disponível: {available_balance}, Solicitado: {amount}")
                return None
            
            # Valor mínimo para saque
            min_withdrawal = 10.0
            if amount < min_withdrawal:
                logger.warning(f"Valor mínimo para saque: R$ {min_withdrawal}")
                return None
            
            # Gerar ID da solicitação
            withdrawal_id = str(uuid.uuid4())
            
            # Criar solicitação de saque
            withdrawal_data = {
                'id': withdrawal_id,
                'creator_id': creator_id,
                'amount': amount,
                'currency': 'BRL',
                'payment_info': payment_info,
                'status': 'pending',
                'requested_at': datetime.now(),
                'updated_at': datetime.now(),
                
                # Dados para processamento
                'processing_fee': amount * 0.02,  # Taxa de processamento 2%
                'net_amount': amount * 0.98,
                'estimated_processing_time': '1-3 dias úteis'
            }
            
            # Usar transação para garantir consistência
            transaction = self.db.transaction()
            
            @firestore.transactional
            def request_withdrawal_transaction(transaction):
                # Criar solicitação de saque
                withdrawal_ref = self.db.collection('withdrawals').document(withdrawal_id)
                transaction.set(withdrawal_ref, withdrawal_data)
                
                # Marcar ganhos como "processing"
                earnings_query = self.db.collection(self.earnings_collection)\
                    .where('creator_id', '==', creator_id)\
                    .where('status', '==', 'pending_withdrawal')\
                    .limit(100)  # Processar em lotes
                
                earnings = earnings_query.get()
                
                amount_to_process = amount
                for earning_doc in earnings:
                    if amount_to_process <= 0:
                        break
                    
                    earning_data = earning_doc.to_dict()
                    earning_amount = earning_data.get('amount', 0.0)
                    
                    if earning_amount <= amount_to_process:
                        # Marcar todo o ganho como processando
                        transaction.update(earning_doc.reference, {
                            'status': 'processing',
                            'withdrawal_id': withdrawal_id,
                            'updated_at': datetime.now()
                        })
                        amount_to_process -= earning_amount
                    else:
                        # Dividir o ganho (caso raro)
                        # Por simplicidade, vamos processar o valor total
                        transaction.update(earning_doc.reference, {
                            'status': 'processing',
                            'withdrawal_id': withdrawal_id,
                            'updated_at': datetime.now()
                        })
                        break
                
                return withdrawal_id
            
            result_id = request_withdrawal_transaction(transaction)
            
            logger.info(f"Solicitação de saque criada: {withdrawal_id} - R$ {amount}")
            
            # Registrar atividade
            await self._log_user_activity(creator_id, 'withdrawal_requested', {
                'withdrawal_id': withdrawal_id,
                'amount': amount,
                'net_amount': withdrawal_data['net_amount']
            })
            
            return withdrawal_id
            
        except Exception as e:
            logger.error(f"Erro ao solicitar saque para criador {creator_id}: {e}")
            return None
    
    async def get_withdrawal_status(self, withdrawal_id: str) -> Optional[Dict]:
        """
        Obtém status de uma solicitação de saque.
        
        Args:
            withdrawal_id: ID da solicitação de saque
            
        Returns:
            Dict: Status da solicitação ou None se não encontrada
        """
        try:
            withdrawal_ref = self.db.collection('withdrawals').document(withdrawal_id)
            withdrawal_doc = withdrawal_ref.get()
            
            if not withdrawal_doc.exists:
                return None
            
            withdrawal_data = withdrawal_doc.to_dict()
            withdrawal_data['id'] = withdrawal_id
            
            return withdrawal_data
            
        except Exception as e:
            logger.error(f"Erro ao obter status do saque {withdrawal_id}: {e}")
            return None
    
    async def get_monetization_stats(self, creator_id: int) -> Dict:
        """
        Obtém estatísticas de monetização de um criador.
        
        Args:
            creator_id: ID do criador
            
        Returns:
            Dict: Estatísticas de monetização
        """
        try:
            # Ganhos por período
            earnings_30d = await self.get_creator_earnings(creator_id, 30)
            earnings_7d = await self.get_creator_earnings(creator_id, 7)
            earnings_today = await self.get_creator_earnings(creator_id, 1)
            
            # Posts monetizados - buscar diretamente do Firestore
            posts_query = self.db.collection(self.posts_collection)\
                .where('creator_id', '==', creator_id)\
                .where('status', '==', 'active')\
                .limit(1000)
            
            user_posts_docs = posts_query.get()
            user_posts = [doc.to_dict() for doc in user_posts_docs]
            
            monetized_posts = [
                post for post in user_posts 
                if post.get('monetization', {}).get('enabled', False)
            ]
            
            # Transações por posts
            total_transactions = 0
            total_revenue = 0.0
            
            for post in monetized_posts:
                post_transactions = self.db.collection(self.transactions_collection)\
                    .where('post_id', '==', post['id'])\
                    .where('status', '==', 'completed')\
                    .get()
                
                post_transaction_count = len(post_transactions)
                post_revenue = sum(
                    doc.to_dict().get('amount', 0.0) for doc in post_transactions
                )
                
                total_transactions += post_transaction_count
                total_revenue += post_revenue
            
            # Calcular métricas
            conversion_rate = 0.0
            if user_posts:
                total_views = sum(post.get('view_count', 0) for post in user_posts)
                if total_views > 0:
                    conversion_rate = (total_transactions / total_views) * 100
            
            stats = {
                'creator_id': creator_id,
                'earnings': {
                    'today': earnings_today.get('total_earnings_period', 0.0),
                    '7_days': earnings_7d.get('total_earnings_period', 0.0),
                    '30_days': earnings_30d.get('total_earnings_period', 0.0),
                    'lifetime': earnings_30d.get('total_lifetime_earnings', 0.0),
                    'pending_withdrawal': earnings_30d.get('pending_withdrawal', 0.0)
                },
                'posts': {
                    'total': len(user_posts),
                    'monetized': len(monetized_posts),
                    'monetization_rate': (len(monetized_posts) / max(len(user_posts), 1)) * 100
                },
                'transactions': {
                    'total_count': total_transactions,
                    'total_revenue': total_revenue,
                    'average_transaction_value': total_revenue / max(total_transactions, 1),
                    'conversion_rate': conversion_rate
                },
                'performance': {
                    'best_performing_post': None,  # Implementar se necessário
                    'average_price': 0.0,  # Calcular preço médio dos posts
                    'repeat_customers': 0  # Implementar se necessário
                }
            }
            
            # Calcular preço médio
            if monetized_posts:
                total_price = sum(
                    post.get('monetization', {}).get('price', 0.0) 
                    for post in monetized_posts
                )
                stats['performance']['average_price'] = total_price / len(monetized_posts)
            
            logger.info(f"Estatísticas de monetização calculadas para criador {creator_id}")
            return stats
            
        except Exception as e:
            logger.error(f"Erro ao obter estatísticas de monetização do criador {creator_id}: {e}")
            return {}
    
    async def _notify_creator_earnings(self, post_id: str, earnings_id: str):
        """Notifica o criador sobre novos ganhos."""
        try:
            # Implementar notificação via bot ou email
            # Por enquanto, apenas log
            logger.info(f"Novo ganho registrado para post {post_id}: {earnings_id}")
            
        except Exception as e:
            logger.error(f"Erro ao notificar criador sobre ganhos: {e}")
    
    async def _log_user_activity(self, user_id: int, activity_type: str, metadata: Dict):
        """Registra atividade do usuário."""
        try:
            activity_data = {
                'user_id': user_id,
                'type': activity_type,
                'metadata': metadata,
                'timestamp': datetime.now()
            }
            
            self.db.collection('user_activities').add(activity_data)
            
        except Exception as e:
            logger.error(f"Erro ao registrar atividade do usuário {user_id}: {e}")
    
    async def validate_payment_webhook(self, webhook_data: Dict) -> bool:
        """
        Valida webhook de pagamento do gateway.
        
        Args:
            webhook_data: Dados do webhook
            
        Returns:
            bool: True se o webhook é válido
        """
        try:
            # Implementar validação específica do gateway (Stripe, PagSeguro, etc.)
            # Por enquanto, validação básica
            
            required_fields = ['transaction_id', 'status', 'amount']
            for field in required_fields:
                if field not in webhook_data:
                    logger.error(f"Campo obrigatório ausente no webhook: {field}")
                    return False
            
            # Verificar se a transação existe
            transaction_id = webhook_data['transaction_id']
            transaction_ref = self.db.collection(self.transactions_collection).document(transaction_id)
            transaction_doc = transaction_ref.get()
            
            if not transaction_doc.exists:
                logger.error(f"Transação não encontrada para webhook: {transaction_id}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar webhook de pagamento: {e}")
            return False
    
    async def process_payment_webhook(self, webhook_data: Dict) -> bool:
        """
        Processa webhook de pagamento confirmado.
        
        Args:
            webhook_data: Dados do webhook
            
        Returns:
            bool: True se processado com sucesso
        """
        try:
            # Se vier evento bruto do Stripe, converter para formato interno
            if ('stripe_event' in webhook_data or 'raw_payload' in webhook_data) and StripeService:
                try:
                    stripe_service = StripeService()
                    if getattr(stripe_service, 'enabled', False):
                        if 'raw_payload' in webhook_data and 'stripe_signature' in webhook_data:
                            event = stripe_service.construct_webhook_event(
                                payload=webhook_data['raw_payload'],
                                signature_header=webhook_data['stripe_signature']
                            )
                            internal = stripe_service.to_internal_webhook(event)
                        else:
                            internal = stripe_service.to_internal_webhook(webhook_data.get('stripe_event'))
                        if internal:
                            webhook_data = internal
                        else:
                            logger.error("Falha ao converter webhook do Stripe para formato interno")
                            return False
                except Exception as e:
                    logger.error(f"Erro ao tratar webhook do Stripe: {e}")
                    return False

            if not await self.validate_payment_webhook(webhook_data):
                return False

            transaction_id = webhook_data['transaction_id']
            status = webhook_data['status']
            
            if status == 'completed' or status == 'paid':
                # Processar pagamento confirmado
                payment_data = {
                    'payment_method': webhook_data.get('payment_method'),
                    'gateway_transaction_id': webhook_data.get('gateway_transaction_id'),
                    'gateway_status': status
                }
                
                return await self.process_payment(transaction_id, payment_data)
            
            elif status == 'failed' or status == 'cancelled':
                # Marcar transação como falhada
                transaction_ref = self.db.collection(self.transactions_collection).document(transaction_id)
                transaction_ref.update({
                    'status': 'failed',
                    'failed_at': datetime.now(),
                    'updated_at': datetime.now(),
                    'failure_reason': webhook_data.get('failure_reason', 'Payment failed')
                })
                
                logger.info(f"Transação marcada como falhada: {transaction_id}")
                return True
            
            else:
                logger.warning(f"Status de webhook não reconhecido: {status}")
                return False
            
        except Exception as e:
            logger.error(f"Erro ao processar webhook de pagamento: {e}")
            return False