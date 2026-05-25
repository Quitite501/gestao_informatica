"""
Extrator de dados de Nota Fiscal
Suporta: XML NF-e (SEFAZ) e PDF (fallback)
"""

import re
import xml.etree.ElementTree as ET
from datetime import datetime
from decimal import Decimal, InvalidOperation


# Namespaces da NF-e SEFAZ
NS = {
    'nfe': 'http://www.portalfiscal.inf.br/nfe',
    'nfeProc': 'http://www.portalfiscal.inf.br/nfe',
}


def extrair_xml(arquivo):
    """Extrai dados do XML NF-e padrão SEFAZ"""
    try:
        tree = ET.parse(arquivo)
        root = tree.getroot()
        
        # Detectar namespace dinamicamente
        tag = root.tag
        ns = ''
        if '{' in tag:
            ns = tag.split('}')[0] + '}'
        
        def find(path):
            """Busca elemento com ou sem namespace"""
            el = root.find(f'.//{ns}{path}')
            if el is None:
                el = root.find(f'.//{path}')
            return el.text.strip() if el is not None and el.text else None
        
        # Número da NF
        numero = find('nNF')
        serie = find('serie')
        if numero and serie:
            numero = f"{numero.zfill(9)}-{serie}"
        
        # Fornecedor (emitente)
        fornecedor = find('xNome')
        cnpj = find('CNPJ')
        if fornecedor and cnpj:
            cnpj_fmt = f"{cnpj[:2]}.{cnpj[2:5]}.{cnpj[5:8]}/{cnpj[8:12]}-{cnpj[12:]}" if len(cnpj) == 14 else cnpj
            fornecedor = f"{fornecedor} (CNPJ: {cnpj_fmt})"
        
        # Data de emissão
        data_emissao = None
        dh_emi = find('dhEmi') or find('dEmi')
        if dh_emi:
            for fmt in ('%Y-%m-%dT%H:%M:%S%z', '%Y-%m-%dT%H:%M:%S', '%Y-%m-%d'):
                try:
                    dt = datetime.strptime(dh_emi[:19], fmt[:len(dh_emi[:19])])
                    data_emissao = dt.strftime('%Y-%m-%d')
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
        
        # Itens da nota
        itens = []
        for det in root.findall(f'.//{ns}det') or root.findall('.//det'):
            prod = det.find(f'{ns}prod') or det.find('prod')
            if prod is not None:
                xprod = (prod.find(f'{ns}xProd') or prod.find('xProd'))
                qcom = (prod.find(f'{ns}qCom') or prod.find('qCom'))
                vprod = (prod.find(f'{ns}vProd') or prod.find('vProd'))
                item = {
                    'descricao': xprod.text.strip() if xprod is not None else '',
                    'quantidade': qcom.text.strip() if qcom is not None else '1',
                    'valor': vprod.text.strip() if vprod is not None else '0',
                }
                if item['descricao']:
                    itens.append(item)
        
        return {
            'sucesso': True,
            'fonte': 'xml',
            'numero': numero,
            'fornecedor': fornecedor,
            'data_emissao': data_emissao,
            'valor_total': valor_total,
            'itens': itens,
        }
    
    except Exception as e:
        return {'sucesso': False, 'erro': str(e), 'fonte': 'xml'}


def extrair_pdf(arquivo):
    """Extrai dados de NF via PDF usando pdfplumber"""
    try:
        import pdfplumber
        
        texto = ''
        with pdfplumber.open(arquivo) as pdf:
            for page in pdf.pages:
                texto += (page.extract_text() or '') + '\n'
        
        if not texto.strip():
            return {'sucesso': False, 'erro': 'PDF sem texto extraível (pode ser imagem)', 'fonte': 'pdf'}
        
        # Extrair número da NF
        numero = None
        for pattern in [
            r'N[úu]mero\s*[:\.]?\s*(\d+)',
            r'NF[- ]?e?\s*[:\.]?\s*(\d+)',
            r'Nota\s+Fiscal\s+[:\.]?\s*(\d+)',
            r'N[ºo°]\s*(\d+)',
        ]:
            m = re.search(pattern, texto, re.IGNORECASE)
            if m:
                numero = m.group(1).zfill(9)
                break
        
        # Extrair fornecedor/emitente
        fornecedor = None
        for pattern in [
            r'Emitente[:\s]+([A-Z][^\n]{5,60})',
            r'Raz[ãa]o\s+Social[:\s]+([A-Z][^\n]{5,60})',
            r'Empresa[:\s]+([A-Z][^\n]{5,60})',
        ]:
            m = re.search(pattern, texto, re.IGNORECASE)
            if m:
                fornecedor = m.group(1).strip()
                break
        
        # Extrair data
        data_emissao = None
        for pattern in [
            r'Data\s+(?:de\s+)?[Ee]miss[ãa]o[:\s]+(\d{2}/\d{2}/\d{4})',
            r'Emiss[ãa]o[:\s]+(\d{2}/\d{2}/\d{4})',
            r'(\d{2}/\d{2}/\d{4})',
        ]:
            m = re.search(pattern, texto, re.IGNORECASE)
            if m:
                try:
                    dt = datetime.strptime(m.group(1), '%d/%m/%Y')
                    data_emissao = dt.strftime('%Y-%m-%d')
                    break
                except ValueError:
                    continue
        
        # Extrair valor total
        valor_total = None
        for pattern in [
            r'Valor\s+Total\s+da\s+Nota[:\s]+R?\$?\s*([\d.,]+)',
            r'TOTAL\s+DA\s+NOTA[:\s]+R?\$?\s*([\d.,]+)',
            r'Valor\s+Total[:\s]+R?\$?\s*([\d.,]+)',
            r'R\$\s*([\d.]+,\d{2})',
        ]:
            m = re.search(pattern, texto, re.IGNORECASE)
            if m:
                v = m.group(1).replace('.', '').replace(',', '.')
                try:
                    valor_total = str(Decimal(v))
                    break
                except InvalidOperation:
                    continue
        
        return {
            'sucesso': True,
            'fonte': 'pdf',
            'numero': numero,
            'fornecedor': fornecedor,
            'data_emissao': data_emissao,
            'valor_total': valor_total,
            'itens': [],
            'texto_bruto': texto[:500],
        }
    
    except Exception as e:
        return {'sucesso': False, 'erro': str(e), 'fonte': 'pdf'}


def extrair_nota_fiscal(arquivo, nome_arquivo=''):
    """Detecta tipo do arquivo e extrai dados automaticamente"""
    nome = (nome_arquivo or '').lower()
    
    if nome.endswith('.xml'):
        return extrair_xml(arquivo)
    elif nome.endswith('.pdf'):
        return extrair_pdf(arquivo)
    else:
        # Tentar XML primeiro, depois PDF
        try:
            resultado = extrair_xml(arquivo)
            if resultado['sucesso']:
                return resultado
        except Exception:
            pass
        arquivo.seek(0)
        return extrair_pdf(arquivo)


# Palavras-chave que indicam software/licença nos itens da NF
PALAVRAS_SOFTWARE = [
    'licença', 'licenca', 'software', 'windows', 'office', 'antivirus',
    'antivírus', 'adobe', 'autocad', 'corel', 'programa', 'sistema',
    'aplicativo', 'app', 'suite', 'subscription', 'assinatura',
    'microsoft', 'google', 'oracle', 'sap', 'totvs', 'linux',
    'acrobat', 'photoshop', 'word', 'excel', 'powerpoint', 'outlook',
]


def detectar_itens_software(itens):
    """
    Analisa lista de itens da NF e identifica possíveis licenças de software.
    Retorna lista de itens com flag is_software=True/False
    """
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
