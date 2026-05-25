"""
Extrator de dados de Nota Fiscal
Suporta: XML NF-e (SEFAZ), NFS-e (PDF), NF-e (PDF)
"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, InvalidOperation


# Namespaces NF-e SEFAZ
NS_NFE = 'http://www.portalfiscal.inf.br/nfe'

# Palavras-chave de software para detecÃ§Ã£o automÃ¡tica
PALAVRAS_SOFTWARE = [
    'licenÃ§a', 'licenca', 'software', 'windows', 'office', 'antivirus',
    'antivÃ­rus', 'adobe', 'autocad', 'corel', 'programa', 'sistema',
    'aplicativo', 'app', 'suite', 'subscription', 'assinatura',
    'microsoft', 'google', 'oracle', 'sap', 'totvs', 'linux',
    'acrobat', 'photoshop', 'word', 'excel', 'powerpoint', 'outlook',
    'server', 'sql', 'cal', 'esd', 'oem', 'licenciamento', 'cessÃ£o',
]


# ============================================================================
# EXTRATOR XML NF-e
# ============================================================================

def extrair_xml(arquivo):
    """Extrai dados do XML NF-e padrÃ£o SEFAZ"""
    try:
        tree = ET.parse(arquivo)
        root = tree.getroot()

        tag = root.tag
        ns = ''
        if '{' in tag:
            ns = tag.split('}')[0] + '}'

        def find(path):
            el = root.find(f'.//{ns}{path}')
            if el is None:
                el = root.find(f'.//{path}')
            return el.text.strip() if el is not None and el.text else None

        # NÃºmero + SÃ©rie
        numero = find('nNF')
        serie = find('serie')
        if numero and serie:
            numero = f"{numero.zfill(9)}-{serie}"

        # Fornecedor
        fornecedor = find('xNome')
        cnpj = find('CNPJ')
        if fornecedor and cnpj and len(cnpj) == 14:
            cnpj_fmt = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}"
            fornecedor = f"{fornecedor} (CNPJ: {cnpj_fmt})"

        # Data de emissÃ£o
        data_emissao = None
        dh_emi = find('dhEmi') or find('dEmi')
        if dh_emi:
            for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
                try:
                    data_emissao = datetime.strptime(dh_emi[:10], '%Y-%m-%d').strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue

        # Valor total
        valor_total = None
        v_nf = find('vNF')
        if v_nf:
            try:
                valor_total = str(Decimal(v_nf))
            except InvalidOperation:
                pass

        # Itens
        itens = []
        for det in root.findall(f'.//{ns}det') or root.findall('.//det'):
            prod = det.find(f'{ns}prod') or det.find('prod')
            if prod is not None:
                xprod = prod.find(f'{ns}xProd') or prod.find('xProd')
                qcom = prod.find(f'{ns}qCom') or prod.find('qCom')
                vprod = prod.find(f'{ns}vProd') or prod.find('vProd')
                item = {
                    'descricao': xprod.text.strip() if xprod is not None else '',
                    'quantidade': qcom.text.strip() if qcom is not None else '1',
                    'valor': vprod.text.strip() if vprod is not None else '0',
                }
                if item['descricao']:
                    itens.append(item)

        return {
            'sucesso': True,
            'tipo': 'nfe',
            'fonte': 'xml',
            'numero': numero,
            'fornecedor': fornecedor,
            'data_emissao': data_emissao,
            'valor_total': valor_total,
            'itens': itens,
        }

    except Exception as e:
        return {'sucesso': False, 'erro': str(e), 'fonte': 'xml'}


# ============================================================================
# EXTRATOR PDF â NFS-e (Nota de ServiÃ§o Municipal)
# ============================================================================

def extrair_nfse_pdf(texto):
    """Extrai dados de NFS-e municipal - suporta texto normal e concatenado"""
    dados = {'tipo': 'nfse'}

    # Número: "NúmerodaNFS-e ... \n431" OU "Número da NFS-e\n431"
    m = re.search(r'N.{0,5}merodaNFS-e[^\n]*\n(\d+)\s', texto)
    if not m:
        m = re.search(r'N[úu]mero da NFS-e\s*\n?\s*(\d+)', texto, re.IGNORECASE)
    if m:
        dados['numero'] = m.group(1).zfill(9)

    # Fornecedor: CNPJ + nome concatenado ou com espaços
    m = re.search(r'(\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2})', texto)
    cnpj = m.group(1) if m else None
    # Nome do emitente: após "Nome/NomeEmpresarial" (concatenado)
    m = re.search(r'Nome/NomeEmpresarial.*?\n(.+?)(?:\s+\S+@\S+|\n)', texto, re.IGNORECASE)
    if not m:
        m = re.search(r'Nome / Nome Empresarial\s*\n([^\n]{5,100})', texto, re.IGNORECASE)
    if m:
        nome = m.group(1).strip()
        # Limpar CNPJ do inicio do nome (ex: "11.401.723HELCIO..." -> "HELCIO...")
        nome_limpo = re.sub(r'^[\d.\-/]+', '', nome).strip()
        if not nome_limpo:
            nome_limpo = nome
        dados['fornecedor'] = f"{nome_limpo} (CNPJ: {cnpj})" if cnpj else nome_limpo

    # Data: "CompetênciadaNFS-e...\n...DD/MM/YYYY" ou direto
    m = re.search(r'Compet.{0,5}nciaNFS-e[^\n]*\n[^\n]*?(\d{2}/\d{2}/\d{4})', texto)
    if not m:
        m = re.search(r'Compet[êe]ncia da NFS-e\s*\n?\s*(\d{2}/\d{2}/\d{4})', texto, re.IGNORECASE)
    if not m:
        m = re.search(r'(\d{2}/\d{2}/\d{4})', texto)
    if m:
        try:
            dados['data_emissao'] = datetime.strptime(m.group(1), '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Valor: "ValorLíquidodaNFS-e\n...R$5.494,30" ou "R$ 5.494,30"
    m = re.search(r'ValorL.{0,5}quidodaNFS-e[^\n]*\n[^\n]*?R\$([\d.,]+)', texto)
    if not m:
        m = re.search(r'Valor L[íi]quido da NFS-e[^\n]*\n?[^\n]*?R\$\s*([\d.,]+)', texto, re.IGNORECASE)
    if not m:
        # Pegar último R$ valor do texto (geralmente é o valor total)
        matches = re.findall(r'R\$([\d.,]+)', texto)
        if matches:
            # Usar o último valor encontrado
            for v in reversed(matches):
                try:
                    val = Decimal(v.replace('.','').replace(',','.'))
                    if val > 0:
                        m = type('M', (), {'group': lambda self, x: v})()
                        break
                except Exception:
                    continue
    if m:
        try:
            val = Decimal(m.group(1).replace('.','').replace(',','.'))
            if val > 0:
                dados['valor_total'] = str(val)
        except InvalidOperation:
            pass

    # Itens: após "DescriçãodoServiço" (concatenado) ou "Descrição do Serviço"
    itens = []
    m = re.search(r'Descri.{0,5}odoServi.o\s*\n(.*?)(?:TRIBUTA|\Z)', texto, re.IGNORECASE | re.DOTALL)
    if not m:
        m = re.search(r'Descri[çc][ãa]o do Servi[çc]o\s*\n(.*?)(?:\n[A-Z]{4,}|\Z)', texto, re.IGNORECASE | re.DOTALL)
    if m:
        bloco = m.group(1).strip()
        for linha in bloco.splitlines():
            linha = linha.strip()
            if not linha or len(linha) < 4:
                continue
            # Remover traço inicial: "-01LICENÇA..." ou "- 01 LICENÇA..."
            linha = re.sub(r'^-\s*', '', linha).strip()
            # Extrair quantidade: "01LICENÇA..." ou "01 LICENÇA..."
            qtd_m = re.match(r'^(\d{1,2})\s*(.+)', linha)
            if qtd_m:
                qtd = int(qtd_m.group(1))
                descricao = qtd_m.group(2).strip()
            else:
                qtd = 1
                descricao = linha
            if len(descricao) > 3:
                itens.append({
                    'descricao': descricao,
                    'quantidade': str(qtd),
                    'valor': '0',
                })
    dados['itens'] = itens
    return dados


def extrair_nfe_pdf(texto):
    """Extrai dados de NF-e de produtos (DANFE) - multiplos formatos"""
    dados = {'tipo': 'nfe'}

    # Numero: Nx:638381 onde x pode ser o simbolo ordinal masculino (0xba)
    m = re.search(r'Nº[s:]*(\d{4,9})', texto)
    if not m:
        m = re.search(r'N[Uu]mero[\s:]+(\d{1,9})\b', texto, re.IGNORECASE)
    if m:
        num = m.group(1)
        if len(num) <= 9:
            dados['numero'] = num.zfill(9)

    # Fornecedor: DANFE tem "RECEBEMOS DE {NOME} OS PRODUTOS"
    m = re.search(r'RECEBEMOS DE\s+(.+?)\s+OS PRODUTOS', texto, re.IGNORECASE)
    if not m:
        m = re.search(r'RECEBEMOS DE\s+(.+?)\s+OS SERVI', texto, re.IGNORECASE)
    if m:
        dados['fornecedor'] = m.group(1).strip()

    # Data: EMISSAO: 12-02-2026 ou 12/02/2026
    m = re.search(r'EMISS[^\s]{0,5}[\s:]+([\d]{2}[-/][\d]{2}[-/][\d]{4})', texto, re.IGNORECASE)
    if m:
        try:
            dados['data_emissao'] = datetime.strptime(m.group(1).replace('-','/'), '%d/%m/%Y').strftime('%Y-%m-%d')
        except ValueError:
            pass

    # Valor: VALOR TOTAL: R$ 3.473,16
    m = re.search(r'VALOR TOTAL[\s:]+R\$\s*([\d.,]+)', texto, re.IGNORECASE)
    if not m:
        m = re.search(r'Valor Total[\s:]+R?\$?\s*([\d.,]+)', texto, re.IGNORECASE)
    if m:
        try:
            val = Decimal(m.group(1).replace('.','').replace(',','.'))
            if val > 0:
                dados['valor_total'] = str(val)
        except InvalidOperation:
            pass

    dados['itens'] = []
    return dados


def detectar_tipo_nf(texto):
    """Detecta se o PDF Ã© NFS-e ou NF-e"""
    texto_lower = texto.lower()
    if any(kw in texto_lower for kw in ['nfs-e', 'nota fiscal de serviÃ§o', 'danfse', 'nfse']):
        return 'nfse'
    if any(kw in texto_lower for kw in ['danfe', 'nf-e', 'nota fiscal eletrÃ´nica']):
        return 'nfe'
    # HeurÃ­stica: NFS-e tem "DescriÃ§Ã£o do ServiÃ§o"
    if 'descriÃ§Ã£o do serviÃ§o' in texto_lower or 'descricao do servico' in texto_lower:
        return 'nfse'
    return 'nfe'  # fallback


# ============================================================================
# EXTRATOR PDF PRINCIPAL
# ============================================================================

def extrair_pdf(arquivo):
    """Extrai dados de NF via PDF â detecta NFS-e ou NF-e automaticamente"""
    try:
        import pdfplumber

        texto = ''
        with pdfplumber.open(arquivo) as pdf:
            for page in pdf.pages:
                texto += (page.extract_text() or '') + '\n'

        if not texto.strip():
            return {'sucesso': False, 'erro': 'PDF sem texto extraÃ­vel (pode ser imagem digitalizada)', 'fonte': 'pdf'}

        tipo = detectar_tipo_nf(texto)

        if tipo == 'nfse':
            dados = extrair_nfse_pdf(texto)
        else:
            dados = extrair_nfe_pdf(texto)

        return {
            'sucesso': True,
            'fonte': 'pdf',
            'texto_bruto': texto[:800],
            **dados,
        }

    except Exception as e:
        return {'sucesso': False, 'erro': str(e), 'fonte': 'pdf'}


# ============================================================================
# DETECÃÃO DE SOFTWARE NOS ITENS
# ============================================================================

def detectar_itens_software(itens):
    """Analisa itens da NF e identifica possÃ­veis licenÃ§as de software"""
    resultado = []
    for item in itens:
        descricao = item.get('descricao', '').lower()
        is_software = any(kw in descricao for kw in PALAVRAS_SOFTWARE)
        resultado.append({
            **item,
            'is_software': is_software,
            'sugestao_nome': item.get('descricao', '').title()[:150],
            'sugestao_qtd': int(float(item.get('quantidade', 1) or 1)),
        })
    return resultado


# ============================================================================
# ENTRADA PRINCIPAL
# ============================================================================

def extrair_nota_fiscal(arquivo, nome_arquivo=''):
    """Detecta tipo do arquivo e extrai dados automaticamente"""
    nome = (nome_arquivo or '').lower()

    if nome.endswith('.xml'):
        return extrair_xml(arquivo)
    elif nome.endswith('.pdf'):
        return extrair_pdf(arquivo)
    else:
        try:
            resultado = extrair_xml(arquivo)
            if resultado.get('sucesso'):
                return resultado
        except Exception:
            pass
        try:
            arquivo.seek(0)
        except Exception:
            pass
        return extrair_pdf(arquivo)
