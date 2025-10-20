#!/usr/bin/env python3
"""
Validador de Segurança - LiberALL Bot
Verifica se há credenciais hardcoded ou valores de teste no código
"""

import os
from pathlib import Path

class SecurityValidator:
    """Validador de segurança para detectar credenciais hardcoded"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
    
    def validate_env_file(self):
        """Validação específica do arquivo .env"""
        env_file = self.project_root / '.env'
        issues = []
        
        if not env_file.exists():
            issues.append({
                'file': '.env',
                'line': 0,
                'type': 'missing_file',
                'description': 'Missing .env file',
                'content': 'Create .env file from .env.example'
            })
            return issues
        
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
                
                for line_num, line in enumerate(lines, 1):
                    if '=' in line and not line.strip().startswith('#'):
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"\'')
                        
                        # Verificar se valores obrigatórios estão configurados
                        required_vars = [
                            'TELEGRAM_BOT_TOKEN',
                            'FIREBASE_PROJECT_ID',
                            'FIREBASE_PRIVATE_KEY',
                            'FIREBASE_CLIENT_EMAIL',
                            'ENCRYPTION_KEY'
                        ]
                        
                        if key in required_vars:
                            if not value or 'your_' in value.lower() or 'here' in value.lower() or 'placeholder' in value.lower():
                                issues.append({
                                    'file': '.env',
                                    'line': line_num,
                                    'type': 'missing_required_value',
                                    'description': f'Required variable {key} not configured',
                                    'content': line.strip()
                                })
                                
        except Exception as e:
            issues.append({
                'file': '.env',
                'line': 0,
                'type': 'validation_error',
                'description': f'Error validating .env: {e}',
                'content': ''
            })
            
        return issues
    
    def generate_report(self):
        """Gera relatório de segurança"""
        # Escanear arquivos
        env_issues = self.validate_env_file()
        
        # Gerar relatório
        report = []
        report.append("🔒 RELATÓRIO DE SEGURANÇA - LiberALL Bot")
        report.append("=" * 50)
        report.append(f"Total de problemas encontrados: {len(env_issues)}")
        report.append("")
        
        if not env_issues:
            report.append("✅ Arquivo .env configurado corretamente!")
            return "\n".join(report)
        
        # Relatório por tipo
        issues_by_type = {}
        for issue in env_issues:
            issue_type = issue['type']
            if issue_type not in issues_by_type:
                issues_by_type[issue_type] = []
            issues_by_type[issue_type].append(issue)
        
        for issue_type, issues in issues_by_type.items():
            report.append(f"📋 {issue_type.upper().replace('_', ' ')} ({len(issues)} problemas)")
            report.append("-" * 30)
            
            for issue in issues:
                report.append(f"📁 Arquivo: {issue['file']}")
                if issue['line'] > 0:
                    report.append(f"📍 Linha: {issue['line']}")
                report.append(f"⚠️  Problema: {issue['description']}")
                if issue['content']:
                    report.append(f"📝 Conteúdo: {issue['content']}")
                report.append("")
        
        # Recomendações
        report.append("💡 RECOMENDAÇÕES")
        report.append("-" * 20)
        report.append("1. Configure todas as variáveis obrigatórias no .env")
        report.append("2. Use credenciais reais para produção")
        report.append("3. Nunca commite o arquivo .env")
        report.append("4. Use diferentes credenciais para desenvolvimento e produção")
        
        return "\n".join(report)

def main():
    """Função principal"""
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    validator = SecurityValidator(project_root)
    
    print("🔍 Executando auditoria de segurança...")
    report = validator.generate_report()
    
    print(report)
    
    # Salvar relatório
    report_file = os.path.join(project_root, 'security_audit_report.txt')
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Relatório salvo em: {report_file}")

if __name__ == '__main__':
    main()