import asyncio
import logging
import os
import signal
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.exceptions import TelegramBadRequest, TelegramConflictError, TelegramUnauthorizedError
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from dotenv import load_dotenv
from config import BOT_TOKEN, BOT_USERNAME
from utils.validators import validate_telegram_token
from handlers.dm_keyboard_handler import DMKeyboardHandler
from handlers.onboarding_handler import OnboardingHandler
from handlers.posting_handler import PostingHandler
from handlers.post_interaction_handler import PostInteractionHandler
from handlers.menu_handler import MenuHandler
from services.firebase_service import FirebaseService
from services.security_service import SecurityService
from services.monetization_service import MonetizationService
from services.optimized_user_service import OptimizedUserService
from services.post_service import PostService
from services.media_service import MediaService
from services.match_service import MatchService
from utils.error_handler import ErrorHandler
from utils.ui_builder import create_control_panel_keyboard
from constants.callbacks import OnboardingCallbacks

# Carregar variáveis de ambiente
load_dotenv()

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Detectar modo simulação
# Pode ser forçado via variável de ambiente FORCE_SIMULATION
ENV_FORCE_SIMULATION = os.getenv('FORCE_SIMULATION', 'false').lower() in ('true', '1', 'yes', 'on')
SIMULATION_MODE = False
try:
    SIMULATION_MODE = ENV_FORCE_SIMULATION or (not validate_telegram_token(BOT_TOKEN))
except Exception:
    # Em caso de erro na validação, assume simulação para evitar crash
    SIMULATION_MODE = True

# Inicializar bot
class DummySession:
    async def close(self):
        logging.info("DummySession.close() chamado")

class DummyChatMember:
    def __init__(self, status: str = 'administrator'):
        self.status = status

class DummyBot:
    def __init__(self, token: str = "SIM_TOKEN"):
        self.token = token
        self.session = DummySession()

    async def delete_webhook(self, drop_pending_updates: bool = True):
        logging.info("[SIMULAÇÃO] delete_webhook chamado")

    async def send_message(self, chat_id, text, parse_mode=None, reply_markup=None):
        logging.info(f"[SIMULAÇÃO] send_message para {chat_id}: {text[:60]}...")

    async def get_chat_member(self, chat_id, user_id):
        logging.info(f"[SIMULAÇÃO] get_chat_member chat={chat_id} user={user_id}")
        return DummyChatMember('administrator')

    async def get_me(self):
        class Me:
            username = 'liberall_dev'
            first_name = 'LiberALL Dev'
            id = 0
        logging.info("[SIMULAÇÃO] get_me chamado")
        return Me()

    class DummyFile:
        def __init__(self, file_path: str):
            self.file_path = file_path

    async def get_file(self, file_id: str):
        """Simula obtenção de metadados do arquivo no Telegram."""
        logging.info(f"[SIMULAÇÃO] get_file chamado para file_id={file_id}")
        # Retorna um caminho fictício; o MediaService apenas o utiliza para download
        return self.DummyFile(file_path=f"simulated/{file_id}.bin")

    async def download_file(self, file_path: str):
        """Simula download de arquivo do Telegram e retorna bytes."""
        logging.info(f"[SIMULAÇÃO] download_file chamado para file_path={file_path}")
        # Retorna bytes fictícios; o MediaService tratará processamento/erros conforme necessário
        return b"SIMULATED_FILE_BYTES"

    async def send_photo(self, chat_id, photo, caption=None, reply_markup=None, parse_mode=None):
        logging.info(
            f"[SIMULAÇÃO] send_photo para {chat_id}: photo={str(photo)[:30]} caption={(caption or '')[:40]}"
        )

    async def send_video(self, chat_id, video, caption=None, reply_markup=None, parse_mode=None):
        logging.info(
            f"[SIMULAÇÃO] send_video para {chat_id}: video={str(video)[:30]} caption={(caption or '')[:40]}"
        )

    async def send_media_group(self, chat_id, media):
        try:
            count = len(media) if hasattr(media, '__len__') else 'unknown'
        except Exception:
            count = 'unknown'
        logging.info(f"[SIMULAÇÃO] send_media_group para {chat_id} com {count} itens")

if SIMULATION_MODE:
    if ENV_FORCE_SIMULATION:
        logging.warning("🔧 FORCE_SIMULATION ativo. Iniciando em modo de simulação (sem polling).")
    else:
        logging.warning("⚠️ BOT_TOKEN inválido. Iniciando em modo de simulação (sem polling).")
    bot = DummyBot(BOT_TOKEN or "SIM_TOKEN")
    dp = Dispatcher()
else:
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher()

# Flag para controle de shutdown
shutdown_flag = False

# Inicializar serviços
firebase_service = FirebaseService()
security_service = SecurityService()

# Aguardar inicialização do Firebase antes de criar outros serviços
async def init_services():
    """Inicializa todos os serviços e handlers."""
    global monetization_service, user_service, post_service, media_service, match_service, error_handler
    global onboarding_handler, posting_handler, post_interaction_handler, menu_handler, dm_handler
    
    # Inicializar Firebase
    await firebase_service._async_init()
    
    # Criar serviços dependentes
    monetization_service = MonetizationService(firebase_service)
    user_service = OptimizedUserService(firebase_service, security_service, monetization_service)
    post_service = PostService(bot=bot, firebase_service=firebase_service)
    media_service = MediaService(user_service, monetization_service, bot)
    match_service = MatchService(firebase_service)
    error_handler = ErrorHandler()
    
    # Inicializar handlers
    onboarding_handler = OnboardingHandler(bot, user_service, security_service, error_handler)
    posting_handler = PostingHandler(bot, post_service, user_service, error_handler, media_service)
    post_interaction_handler = PostInteractionHandler(bot, user_service, post_service, error_handler, BOT_USERNAME, match_service)
    menu_handler = MenuHandler(user_service, post_service, match_service, None, error_handler)
    dm_handler = DMKeyboardHandler(bot, onboarding_handler, user_service, security_service, error_handler, posting_handler)
    
    # Configurar referências cruzadas
    if hasattr(onboarding_handler, 'set_dm_keyboard_handler'):
        onboarding_handler.set_dm_keyboard_handler(dm_handler)
    if hasattr(dm_handler, 'set_posting_handler'):
        dm_handler.set_posting_handler(posting_handler)
    
    return firebase_service

# Função para inicializar serviços dependentes
def create_dependent_services(firebase_service):
    monetization_service = MonetizationService(firebase_service)
    user_service = OptimizedUserService(firebase_service, security_service, monetization_service)
    post_service = PostService(bot=bot, firebase_service=firebase_service)
    media_service = MediaService(user_service, monetization_service, bot)
    match_service = MatchService(firebase_service)
    error_handler = ErrorHandler()
    return monetization_service, user_service, post_service, media_service, match_service, error_handler

# Variáveis globais para serviços e handlers
monetization_service = None
user_service = None
post_service = None
media_service = None
match_service = None
error_handler = None
onboarding_handler = None
posting_handler = None
post_interaction_handler = None
menu_handler = None
dm_handler = None

def switch_to_simulation():
    """Alterna para modo simulação em tempo de execução mantendo dispatcher atual."""
    global SIMULATION_MODE, bot
    if SIMULATION_MODE:
        return
    logging.warning("⚠️ Falha de autorização do bot. Alternando para modo simulação (sem polling).")
    SIMULATION_MODE = True
    bot = DummyBot(BOT_TOKEN or "SIM_TOKEN")

async def start_command(message: Message):
    """Processa o comando /start com parâmetros de deep link."""
    try:
        # Extrair parâmetros do deep link (aiogram 3.x)
        command_text = message.text or ""
        args = command_text.split()[1:] if len(command_text.split()) > 1 else []
        args_str = " ".join(args) if args else None
        
        # Verificar se é um deep link
        if args_str:
            await dm_handler.handle_deep_link(message, args_str)
            return
        
        # Se não houver parâmetros, iniciar onboarding
        await onboarding_handler.start_onboarding(message)
        
    except Exception as e:
        logger.error(f"Erro no comando start: {e}")
        await error_handler.handle_error(bot, message.chat.id, "Erro ao iniciar.")

async def handle_setupgroup_command(message: Message):
    """Configura o painel de controle anônimo no grupo."""
    try:
        # Verificar se é um grupo
        if message.chat.type not in ['group', 'supergroup']:
            await message.reply("❌ Este comando só pode ser usado em grupos!")
            return
        
        # Verificar se o usuário é admin
        chat_member = await bot.get_chat_member(message.chat.id, message.from_user.id)
        if chat_member.status not in ['creator', 'administrator']:
            await message.reply("❌ Apenas administradores podem usar este comando!")
            return
        
        # Criar teclado inline com deep links
        keyboard = create_control_panel_keyboard(BOT_USERNAME)
        
        # Enviar mensagem com o painel
        await bot.send_message(
            message.chat.id,
            "🎯 <b>Painel de Controle da Comunidade</b>\n\n"
            "Use os botões abaixo para interagir de forma anônima:",
            parse_mode='HTML',
            reply_markup=keyboard
        )
        
        # Tentar deletar o comando original
        try:
            await message.delete()
        except:
            pass
        
    except Exception as e:
        logger.error(f"Erro ao configurar grupo: {e}")
        await error_handler.handle_error(bot, message.chat.id, "Erro ao configurar grupo.")

async def handle_media_message(message: Message):
    """Processa conteúdo para criação de posts."""
    try:
        # Ignorar mensagens de grupos
        if message.chat.type != 'private':
            return
        
        # Processar criação de post
        await posting_handler.handle_post_creation(message)
        
    except Exception as e:
        logger.error(f"Erro ao processar conteúdo: {e}")
        await error_handler.handle_error(bot, message.chat.id, "Erro ao processar conteúdo.")

async def handle_text_message(message: Message):
    """Processa mensagens de texto para onboarding e outras funcionalidades."""
    try:
        # Ignorar mensagens de grupos
        if message.chat.type != 'private':
            return
        
        user_id = message.from_user.id
        
        # Verificar se o usuário está aguardando valor de monetização personalizado
        user_data = await user_service.get_user_data(user_id)
        if user_data and user_data.get('state') == 'AWAITING_MONETIZATION_VALUE':
            await posting_handler.handle_custom_monetization_value(message)
            return
        
        # Verificar se o usuário está aguardando comentário
        if user_data and user_data.get('state') == 'awaiting_comment':
            await post_interaction_handler.handle_comment_text(message, user_id)
            return
        
        # Primeiro, verificar se há fluxo de postagem ativo e processar entrada de criação
        await posting_handler.handle_post_creation(message)
        
        # Em seguida, processar mensagens do onboarding
        await onboarding_handler.handle_onboarding_message(message)
        
    except Exception as e:
        logger.error(f"Erro ao processar mensagem de texto: {e}")
        await error_handler.handle_error(bot, message.chat.id, "Erro ao processar mensagem.")

async def unified_callback_handler(call: types.CallbackQuery):
    """
    Handler unificado e roteador para todos os callbacks da aplicação.
    Analisa o callback_data e delega para o handler apropriado.
    """
    try:
        # Responde ao Telegram imediatamente para o relógio não expirar
        try:
            await call.answer()
        except TelegramBadRequest as e:
            # Callback pode estar expirado; segue processamento sem falhar
            logging.warning(f"Callback answer falhou/expirado: {e}")
        except Exception as e:
            logging.warning(f"Falha ao responder callback: {e}")
        data = call.data or ""
        logging.info(f"Callback recebido: {data}")

        # ===== Onboarding =====
        # Inclui explicitamente 'start_onboarding' para iniciar o fluxo
        if (
            data == "start_onboarding"
            or data.startswith("onboarding_")
            or data in [
                "confirm_age",
                "reject_age",
                "accept_rules",
                "reject_rules",
                "accept_terms",
                "reject_terms",
                "accept_lgpd",
                "reject_lgpd",
                "creator_yes",
                "creator_no",
                "accept_monetization",
                "reject_monetization",
                "group_lite",
                "group_premium",
            ]
            or data.startswith(("state_", "category_", "gender_", "profile_", "rel_"))
            or data == "finish_relationship_selection"
        ):
            await onboarding_handler.handle_onboarding_callback(call)
            return

        # ===== Interações com Posts (formato novo: ação:post:id) =====
        if (data.startswith((
            "match:post:",
            "info:post:",
            "gallery:post:",
            "favorite:post:",
            "comments:post:",
        ))):
            await post_interaction_handler.handle_post_interaction(call)
            return

        # ===== Interações com Posts (formato legado para compatibilidade) =====
        if (data.startswith((
            "match_post_",
            "info_post_",
            "gallery_post_",
            "favorite_post_",
            "comment_post_",
        ))):
            await post_interaction_handler.handle_post_interaction(call)
            return

        # ===== Navegação de Mídia =====
        if data.startswith("nav_media_") or data == "close_media_nav" or data == "noop":
            # Importar e usar MediaNavigationHandler
            from handlers.media_navigation_handler import MediaNavigationHandler
            media_nav_handler = MediaNavigationHandler(bot, post_service, error_handler)
            if data == "close_media_nav":
                await call.message.delete()
                await call.answer("📷 Navegação fechada.")
            elif data == "noop":
                # Botão informativo, apenas responder
                await call.answer()
            else:
                await media_nav_handler.handle_media_navigation(call)
            return

        # ===== Menu Principal =====
        # Encaminhar callbacks que começam com 'menu_' ou 'menu:' para o MenuHandler
        if (data.startswith("menu_") or data.startswith("menu:") or 
            data in ("main_menu", "profile_menu", "settings", "favorites", "help", 
                    "create_post", "view_posts", "matches", "statistics", "gallery", "start_post")):
            logging.info(f"Encaminhando callback do menu para MenuHandler: {data}")
            await menu_handler.handle_callback(call)
            return

        # ===== Fluxo de Postagem (callbacks novos formato ação:alvo) =====
        if data in ("posting:create", "menu:main"):
            if data == "posting:create":
                await posting_handler.handle_callback_query(call)
            elif data == "menu:main":
                await menu_handler.handle_callback(call)
            return

        # ===== Fluxo de Postagem =====
        if (
            data.startswith("post_type_")
            or data.startswith("post_monetize")
            or data.startswith("post_publish:")
            or data in (
                "post_publish",
                "post_cancel",
                "post_preview",
                "post_add_media",
                "post_remove_media",
                "continue_to_preview",
            )
        ):
            await posting_handler.handle_callback_query(call)
            return

        # ===== Monetização =====
        if data.startswith("monetization_") or data.startswith("monetize_"):
            logging.info(f"Encaminhando callback de monetização: {data}")
            await posting_handler.handle_callback_query(call)
            return

        # ===== Roteamento para callbacks de comentários =====
        if data == "cancel_comment":
            await post_interaction_handler.handle_cancel_comment(call)
            return

        # ===== Fallback =====
        logging.warning(f"Nenhum handler encontrado para o callback: {data}")
        await call.answer("Esta opção ainda não foi implementada.", show_alert=True)

    except Exception as e:
        logging.error(f"Erro no handler unificado de callback: {e}", exc_info=True)
        try:
            await call.message.answer("❌ Ocorreu um erro ao processar a sua solicitação. Tente novamente.")
        except:
            pass

# Registrar handlers
from aiogram.filters import Command
from aiogram import F

dp.message.register(start_command, Command(commands=['start']))
dp.message.register(handle_setupgroup_command, Command(commands=['setupgroup']))
dp.message.register(handle_media_message, F.content_type.in_({'photo', 'video', 'document'}))
dp.message.register(handle_text_message, F.text)
dp.callback_query.register(unified_callback_handler)

async def cleanup_bot_instance():
    """Limpa instâncias anteriores do bot."""
    try:
        logger.info("🧹 Limpando instâncias anteriores do bot...")
        
        # Tentar deletar webhook se existir
        try:
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ Webhook removido com sucesso")
        except TelegramUnauthorizedError as e:
            # Token inválido/sem autorização: alterna para simulação
            logger.warning(f"Token sem autorização ao remover webhook: {e}")
            switch_to_simulation()
        except Exception as e:
            # Em simulação ou sem webhook, apenas registra
            logger.debug(f"Webhook não encontrado ou já removido: {e}")
        
        # Aguardar um pouco para garantir que a instância anterior seja finalizada
        await asyncio.sleep(2)
        
    except Exception as e:
        logger.warning(f"Erro durante cleanup: {e}")

def signal_handler(signum, frame):
    """Handler para sinais de sistema."""
    global shutdown_flag
    logger.info(f"Sinal {signum} recebido. Iniciando shutdown graceful...")
    shutdown_flag = True

# Iniciar o bot
async def main():
    """Função principal do bot."""
    try:
        logger.info("🚀 Iniciando LiberALL Bot...")
        
        # Configurar logging estruturado
        setup_structured_logging()
        
        # Inicializar serviços base
        await init_services()
        
        # Usar os serviços globais já inicializados
        global user_service, error_handler, onboarding_handler, menu_handler, posting_handler, post_interaction_handler, dm_handler
        
        # Log de inicialização dos handlers
        logger.info("✅ Handlers inicializados:")
        logger.info(f"  - OnboardingHandler: {type(onboarding_handler).__name__}")
        logger.info(f"  - MenuHandler: {type(menu_handler).__name__}")
        logger.info(f"  - PostingHandler: {type(posting_handler).__name__}")
        logger.info(f"  - PostInteractionHandler: {type(post_interaction_handler).__name__}")
        logger.info(f"  - DMKeyboardHandler: {type(dm_handler).__name__}")
        
        # Configurar handlers de mensagens
        dp.message.register(start_command, Command("start"))
        dp.message.register(handle_setupgroup_command, Command("setupgroup"))
        dp.message.register(handle_media_message, F.content_type.in_({'photo', 'video', 'document'}))
        dp.message.register(handle_text_message, F.text)
        dp.callback_query.register(unified_callback_handler)
        
        # Configurar handlers de sinal para shutdown gracioso
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        if SIMULATION_MODE:
            logger.info("🔧 Modo simulação ativo - Bot não fará polling")
            logger.info("✅ Bot inicializado com sucesso em modo simulação")
            
            # Em modo simulação, manter o processo vivo
            try:
                while not shutdown_flag:
                    await asyncio.sleep(1)
            except KeyboardInterrupt:
                logger.info("🛑 Interrupção detectada")
        else:
            # Iniciar polling
            logger.info("🔄 Iniciando polling...")
            await dp.start_polling(bot, skip_updates=True)
            
    except Exception as e:
        logger.error(f"❌ Erro crítico na inicialização: {e}", exc_info=True)
        raise
    finally:
        # Cleanup
        await cleanup_bot_instance()

def setup_structured_logging():
    """Configura logging estruturado para depuração e telemetria."""
    import json
    import datetime
    
    class StructuredFormatter(logging.Formatter):
        def format(self, record):
            log_entry = {
                'timestamp': datetime.datetime.utcnow().isoformat(),
                'level': record.levelname,
                'module': record.module,
                'function': record.funcName,
                'line': record.lineno,
                'message': record.getMessage(),
                'bot_id': 'liberall_bot'
            }
            
            if hasattr(record, 'user_id'):
                log_entry['user_id'] = record.user_id
            if hasattr(record, 'action'):
                log_entry['action'] = record.action
            if hasattr(record, 'callback_data'):
                log_entry['callback_data'] = record.callback_data
                
            return json.dumps(log_entry, ensure_ascii=False)
    
    # Configurar handler para logs estruturados
    structured_handler = logging.StreamHandler()
    structured_handler.setFormatter(StructuredFormatter())
    
    # Aplicar apenas para logs de nível INFO e superior
    structured_handler.setLevel(logging.INFO)
    
    # Adicionar handler aos loggers principais
    main_loggers = [
        'handlers.onboarding_handler',
        'handlers.menu_handler', 
        'handlers.posting_handler',
        'handlers.post_interaction_handler',
        'main'
    ]
    
    for logger_name in main_loggers:
        logger = logging.getLogger(logger_name)
        logger.addHandler(structured_handler)
        logger.setLevel(logging.INFO)

if __name__ == '__main__':
    asyncio.run(main())