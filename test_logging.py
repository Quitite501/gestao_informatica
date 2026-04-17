import logging
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

logger = logging.getLogger('sistema_ti')

# Testar diferentes níveis de log
logger.info("Teste de log INFO - Sistema de logs ativo")
logger.warning("Teste de log WARNING - Atenção necessária")
logger.error("Teste de log ERROR - Erro detectado no teste")

print("\nLogs gravados com sucesso!")
print("Verifique os arquivos:")
print("- logs/django_info.log")
print("- logs/django_warnings.log")
print("- logs/django_errors.log")
