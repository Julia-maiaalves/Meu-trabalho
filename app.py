import json
from pathlib import Path
from datetime import date
import streamlit as st

ARQUIVO = Path('biblioteca_dados.json')

st.set_page_config(page_title='Biblioteca Escolar', page_icon='📚', layout='centered')
st.title('📚 Sistema de Gerenciamento de Biblioteca Escolar')
st.caption('Protótipo acadêmico para cadastro de livros, usuários, empréstimos e devoluções.')


def carregar_dados():
    if ARQUIVO.exists():
        try:
            dados = json.loads(ARQUIVO.read_text(encoding='utf-8'))
            return {"livros": dados.get("livros", []), "usuarios": dados.get("usuarios", []), "emprestimos": dados.get("emprestimos", [])}
        except (json.JSONDecodeError, OSError):
            st.error('Não foi possível ler o arquivo de dados. Um cadastro vazio será iniciado.')
    return {"livros": [], "usuarios": [], "emprestimos": []}


def salvar_dados(dados):
    ARQUIVO.write_text(json.dumps(dados, ensure_ascii=False, indent=2), encoding='utf-8')


def proximo_id(registros):
    return max((item['id'] for item in registros), default=0) + 1


def emprestados_do_livro(dados, livro_id):
    return sum(1 for e in dados['emprestimos'] if e['livro_id'] == livro_id and e['status'] == 'aberto')


dados = carregar_dados()
aba = st.tabs(['Visão geral', 'Cadastrar livro', 'Cadastrar usuário', 'Livros e usuários', 'Empréstimos', 'Devoluções'])

with aba[0]:
    c1, c2, c3 = st.columns(3)
    c1.metric('Livros cadastrados', len(dados['livros']))
    c2.metric('Usuários cadastrados', len(dados['usuarios']))
    c3.metric('Empréstimos em aberto', sum(1 for e in dados['emprestimos'] if e['status'] == 'aberto'))
    st.info('Use as abas acima para cadastrar e consultar os registros.')

with aba[1]:
    st.subheader('Cadastrar livro')
    with st.form('form_livro', clear_on_submit=True):
        titulo = st.text_input('Título *')
        autor = st.text_input('Autor(a) *')
        isbn = st.text_input('ISBN (opcional)')
        quantidade = st.number_input('Quantidade de exemplares', min_value=1, step=1, value=1)
        enviado = st.form_submit_button('Cadastrar livro')
    if enviado:
        if not titulo.strip() or not autor.strip():
            st.error('Título e autor são obrigatórios.')
        else:
            dados['livros'].append({'id': proximo_id(dados['livros']), 'titulo': titulo.strip(), 'autor': autor.strip(), 'isbn': isbn.strip(), 'quantidade': int(quantidade)})
            salvar_dados(dados)
            st.success('Livro cadastrado com sucesso!')
            st.rerun()

with aba[2]:
    st.subheader('Cadastrar usuário')
    with st.form('form_usuario', clear_on_submit=True):
        nome = st.text_input('Nome do usuário *')
        identificacao = st.text_input('Matrícula ou código *')
        enviado = st.form_submit_button('Cadastrar usuário')
    if enviado:
        if not nome.strip() or not identificacao.strip():
            st.error('Nome e identificação são obrigatórios.')
        elif any(u['identificacao'] == identificacao.strip() for u in dados['usuarios']):
            st.error('Já existe usuário com essa identificação.')
        else:
            dados['usuarios'].append({'id': proximo_id(dados['usuarios']), 'nome': nome.strip(), 'identificacao': identificacao.strip()})
            salvar_dados(dados)
            st.success('Usuário cadastrado com sucesso!')
            st.rerun()

with aba[3]:
    st.subheader('Livros e disponibilidade')
    if dados['livros']:
        linhas = []
        for livro in dados['livros']:
            emprestados = emprestados_do_livro(dados, livro['id'])
            linhas.append({'ID': livro['id'], 'Título': livro['titulo'], 'Autor(a)': livro['autor'], 'Exemplares': livro['quantidade'], 'Disponíveis': livro['quantidade'] - emprestados})
        st.dataframe(linhas, use_container_width=True, hide_index=True)
    else:
        st.info('Nenhum livro cadastrado.')
    st.subheader('Usuários cadastrados')
    if dados['usuarios']:
        st.dataframe([{'ID': u['id'], 'Nome': u['nome'], 'Matrícula/código': u['identificacao']} for u in dados['usuarios']], use_container_width=True, hide_index=True)
    else:
        st.info('Nenhum usuário cadastrado.')

with aba[4]:
    st.subheader('Registrar empréstimo')
    livros_disponiveis = [l for l in dados['livros'] if l['quantidade'] - emprestados_do_livro(dados, l['id']) > 0]
    if not livros_disponiveis or not dados['usuarios']:
        st.info('Cadastre pelo menos um livro disponível e um usuário antes de registrar empréstimos.')
    else:
        op_livros = {f"{l['titulo']} (ID {l['id']}) — disponíveis: {l['quantidade'] - emprestados_do_livro(dados, l['id'])}": l['id'] for l in livros_disponiveis}
        op_usuarios = {f"{u['nome']} — código {u['identificacao']}": u['id'] for u in dados['usuarios']}
        with st.form('form_emprestimo'):
            livro_escolhido = st.selectbox('Livro', list(op_livros.keys()))
            usuario_escolhido = st.selectbox('Usuário', list(op_usuarios.keys()))
            enviado = st.form_submit_button('Registrar empréstimo')
        if enviado:
            dados['emprestimos'].append({'id': proximo_id(dados['emprestimos']), 'livro_id': op_livros[livro_escolhido], 'usuario_id': op_usuarios[usuario_escolhido], 'data_emprestimo': date.today().isoformat(), 'data_devolucao': None, 'status': 'aberto'})
            salvar_dados(dados)
            st.success('Empréstimo registrado!')
            st.rerun()
    st.subheader('Empréstimos em aberto')
    abertos = [e for e in dados['emprestimos'] if e['status'] == 'aberto']
    if abertos:
        livros = {l['id']: l['titulo'] for l in dados['livros']}
        usuarios = {u['id']: u['nome'] for u in dados['usuarios']}
        st.dataframe([{'Empréstimo': e['id'], 'Livro': livros.get(e['livro_id'], 'Não encontrado'), 'Usuário': usuarios.get(e['usuario_id'], 'Não encontrado'), 'Data': e['data_emprestimo']} for e in abertos], use_container_width=True, hide_index=True)
    else:
        st.info('Não há empréstimos em aberto.')

with aba[5]:
    st.subheader('Registrar devolução')
    abertos = [e for e in dados['emprestimos'] if e['status'] == 'aberto']
    if not abertos:
        st.info('Não há empréstimos em aberto para devolver.')
    else:
        livros = {l['id']: l['titulo'] for l in dados['livros']}
        usuarios = {u['id']: u['nome'] for u in dados['usuarios']}
        opcoes = {f"Empréstimo {e['id']} — {livros.get(e['livro_id'], 'Livro')} / {usuarios.get(e['usuario_id'], 'Usuário')} — {e['data_emprestimo']}": e['id'] for e in abertos}
        with st.form('form_devolucao'):
            escolha = st.selectbox('Selecione o empréstimo', list(opcoes.keys()))
            enviado = st.form_submit_button('Confirmar devolução')
        if enviado:
            emprestimo_id = opcoes[escolha]
            for e in dados['emprestimos']:
                if e['id'] == emprestimo_id and e['status'] == 'aberto':
                    e['status'] = 'devolvido'
                    e['data_devolucao'] = date.today().isoformat()
                    break
            salvar_dados(dados)
            st.success('Devolução registrada!')
            st.rerun()

st.divider()
st.caption('Protótipo para fins didáticos. Não utilize dados pessoais reais ou sensíveis. Em hospedagens gratuitas, os dados locais podem não ser permanentes; faça cópias de segurança e não use como sistema oficial sem avaliação técnica.')
