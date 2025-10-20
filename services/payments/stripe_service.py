import os
import logging
from typing import Dict, Optional

try:
    import stripe
except Exception:
    stripe = None

logger = logging.getLogger(__name__)


class StripeService:
    """Serviço para integração com Stripe.

    Implementa criação de PaymentIntent usando "destination charge" (Stripe Connect)
    com `application_fee_amount` para split de taxa da plataforma.
    """

    def __init__(self):
        self.enabled = False
        self.secret_key = os.getenv("STRIPE_SECRET_KEY")
        self.publishable_key = os.getenv("STRIPE_PUBLISHABLE_KEY")
        self.webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")
        self.enable_connect = os.getenv("ENABLE_STRIPE_CONNECT", "false").lower() in ("true", "1", "yes", "on")
        self.connect_account_id = os.getenv("STRIPE_CONNECT_ACCOUNT_ID")
        enable_flag = os.getenv("ENABLE_STRIPE", "false").lower() in ("true", "1", "yes", "on")

        if stripe and self.secret_key and enable_flag:
            try:
                stripe.api_key = self.secret_key
                self.enabled = True
                logger.info("StripeService habilitado e inicializado")
            except Exception as e:
                logger.error(f"Falha ao inicializar StripeService: {e}")
                self.enabled = False
        else:
            logger.info("StripeService desabilitado (stripe lib/secret_key/flag ausentes)")

    def create_payment_intent(
        self,
        transaction_id: str,
        amount: float,
        currency: str,
        metadata: Dict,
        platform_fee_percentage: float = 10.0,
        destination_account: Optional[str] = None,
    ) -> Optional[Dict]:
        """Cria um PaymentIntent no Stripe.

        Args:
            transaction_id: ID interno da transação
            amount: valor em unidade decimal (ex.: 19.90)
            currency: moeda (ex.: 'BRL')
            metadata: metadados (user_id, post_id, etc.)
            platform_fee_percentage: taxa da plataforma em %
            destination_account: conta conectada do criador (acct_...)

        Returns:
            Dict com dados do intent ou None em caso de falha
        """
        if not self.enabled or not stripe:
            logger.warning("StripeService não habilitado; pulando criação de PaymentIntent")
            return None

        try:
            # Stripe espera valores em centavos
            amount_cents = int(round(amount * 100))
            application_fee_amount = int(round(amount_cents * (platform_fee_percentage / 100.0)))

            create_kwargs = {
                "amount": amount_cents,
                "currency": currency.lower(),
                "automatic_payment_methods": {"enabled": True},
                "description": f"LiberALL - Transação {transaction_id}",
                "metadata": {"transaction_id": transaction_id, **(metadata or {})},
            }

            # Destination charge via Stripe Connect (se disponível)
            # Usar destino padrão de Stripe Connect se habilitado
            if not destination_account and self.enable_connect and self.connect_account_id:
                destination_account = self.connect_account_id

            if destination_account:
                create_kwargs["application_fee_amount"] = application_fee_amount
                create_kwargs["transfer_data"] = {"destination": destination_account}

            intent = stripe.PaymentIntent.create(**create_kwargs)

            return {
                "payment_intent_id": intent.get("id"),
                "client_secret": intent.get("client_secret"),
                "status": intent.get("status"),
                "currency": intent.get("currency"),
                "amount": intent.get("amount"),
            }
        except Exception as e:
            logger.error(f"Erro ao criar PaymentIntent no Stripe: {e}")
            return None

    def construct_webhook_event(self, payload: bytes, signature_header: str):
        """Valida e constrói evento de webhook do Stripe."""
        if not self.enabled or not stripe:
            raise ValueError("StripeService não habilitado")
        try:
            event = stripe.Webhook.construct_event(payload, signature_header, self.webhook_secret)
            return event
        except Exception as e:
            logger.error(f"Falha na validação do webhook do Stripe: {e}")
            raise

    def to_internal_webhook(self, event: Dict) -> Optional[Dict]:
        """Converte evento Stripe para formato interno de webhook.

        Retorna dict com chaves: transaction_id, status, amount, payment_method, gateway_transaction_id
        """
        try:
            event_type = event.get("type")
            data_obj = (event.get("data", {}) or {}).get("object", {})

            # Preferir PaymentIntent
            if data_obj.get("object") == "payment_intent":
                transaction_id = (data_obj.get("metadata", {}) or {}).get("transaction_id")
                amount = int(data_obj.get("amount", 0)) / 100.0
                status = data_obj.get("status")

                mapped_status = "completed" if status in ("succeeded") else (
                    "failed" if status in ("canceled", "requires_payment_method") else status
                )

                return {
                    "transaction_id": transaction_id,
                    "status": mapped_status,
                    "amount": amount,
                    "payment_method": "stripe",
                    "gateway_transaction_id": data_obj.get("id"),
                }

            # Fallback para charge.succeeded
            if data_obj.get("object") == "charge":
                transaction_id = (data_obj.get("metadata", {}) or {}).get("transaction_id")
                amount = int(data_obj.get("amount", 0)) / 100.0
                status = data_obj.get("status")
                mapped_status = "completed" if status == "succeeded" else status
                return {
                    "transaction_id": transaction_id,
                    "status": mapped_status,
                    "amount": amount,
                    "payment_method": "stripe",
                    "gateway_transaction_id": data_obj.get("payment_intent") or data_obj.get("id"),
                }

            logger.warning(f"Evento Stripe não mapeado: {event_type}")
            return None
        except Exception as e:
            logger.error(f"Erro ao converter webhook do Stripe: {e}")
            return None