import json
from pathlib import Path
from datetime import date

ARQUIVO = Path("biblioteca_dados.json")


def carregar_dados():
    if ARQUIVO.exists():
        try:
            return json.loads(ARQUIVO.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            print("Aviso: não foi possível ler os dados. Um cadastro vazio será iniciado.")
    return {"livros": [], "usuarios": [], "emprestimos": []}


def salvar_dados(dados):
    ARQUIVO.write_text(
        json.dumps(dados, ensure_ascii=False, indent=2),
        encoding="utf-8"
    )


def proximo_id(registros):
    return max((item["id"] for item in registros), default=0) + 1


def cadastrar_livro(dados):
    titulo = input("Título: ").strip()
    autor = input("Autor(a): ").strip()
    isbn = input("ISBN (opcional): ").strip()
    quantidade_txt = input("Quantidade de exemplares: ").strip()

    if not titulo or not autor:
        print("Título e autor são obrigatórios.")
        return
    try:
        quantidade = int(quantidade_txt)
        if quantidade < 1:
            raise ValueError
    except ValueError:
        print("Informe uma quantidade inteira maior que zero.")
        return

    dados["livros"].append({
        "id": proximo_id(dados["livros"]),
        "titulo": titulo,
        "autor": autor,
        "isbn": isbn,
        "quantidade": quantidade
    })
    salvar_dados(dados)
    print("Livro cadastrado com sucesso.")


def cadastrar_usuario(dados):
    nome = input("Nome do usuário: ").strip()
    identificacao = input("Matrícula ou código: ").strip()
    if not nome or not identificacao:
        print("Nome e identificação são obrigatórios.")
        return
    if any(u["identificacao"] == identificacao for u in dados["usuarios"]):
        print("Já existe usuário com essa identificação.")
        return

    dados["usuarios"].append({
        "id": proximo_id(dados["usuarios"]),
        "nome": nome,
        "identificacao": identificacao
    })
    salvar_dados(dados)
    print("Usuário cadastrado com sucesso.")


def listar_livros(dados):
    if not dados["livros"]:
        print("Nenhum livro cadastrado.")
        return
    print("\nID | TÍTULO | AUTOR(A) | DISPONÍVEIS")
    for livro in dados["livros"]:
        emprestados = sum(
            1 for e in dados["emprestimos"]
            if e["livro_id"] == livro["id"] and e["status"] == "aberto"
        )
        disponiveis = livro["quantidade"] - emprestados
        print(f'{livro["id"]} | {livro["titulo"]} | '
              f'{livro["autor"]} | {disponiveis}')


def registrar_emprestimo(dados):
    listar_livros(dados)
    try:
        livro_id = int(input("ID do livro: "))
        usuario_id = int(input("ID do usuário: "))
    except ValueError:
        print("Os identificadores devem ser números inteiros.")
        return

    livro = next((l for l in dados["livros"] if l["id"] == livro_id), None)
    usuario = next((u for u in dados["usuarios"] if u["id"] == usuario_id), None)
    if livro is None or usuario is None:
        print("Livro ou usuário não encontrado.")
        return

    emprestados = sum(
        1 for e in dados["emprestimos"]
        if e["livro_id"] == livro_id and e["status"] == "aberto"
    )
    if emprestados >= livro["quantidade"]:
        print("Não há exemplar disponível para empréstimo.")
        return

    dados["emprestimos"].append({
        "id": proximo_id(dados["emprestimos"]),
        "livro_id": livro_id,
        "usuario_id": usuario_id,
        "data_emprestimo": date.today().isoformat(),
        "data_devolucao": None,
        "status": "aberto"
    })
    salvar_dados(dados)
    print("Empréstimo registrado.")


def registrar_devolucao(dados):
    abertos = [e for e in dados["emprestimos"] if e["status"] == "aberto"]
    if not abertos:
        print("Não há empréstimos em aberto.")
        return
    for e in abertos:
        print(f'Empréstimo {e["id"]}: livro ID {e["livro_id"]}, '
              f'usuário ID {e["usuario_id"]}')
    try:
        emprestimo_id = int(input("ID do empréstimo a devolver: "))
    except ValueError:
        print("Informe um identificador numérico.")
        return

    emprestimo = next(
        (e for e in abertos if e["id"] == emprestimo_id), None
    )
    if emprestimo is None:
        print("Empréstimo em aberto não encontrado.")
        return

    emprestimo["status"] = "devolvido"
    emprestimo["data_devolucao"] = date.today().isoformat()
    salvar_dados(dados)
    print("Devolução registrada.")


def listar_usuarios(dados):
    if not dados["usuarios"]:
        print("Nenhum usuário cadastrado.")
        return
    for usuario in dados["usuarios"]:
        print(f'{usuario["id"]} | {usuario["nome"]} | '
              f'{usuario["identificacao"]}')


def menu():
    dados = carregar_dados()
    while True:
        print("\n=== SISTEMA DE GERENCIAMENTO DE BIBLIOTECA ESCOLAR ===")
        print("1 - Cadastrar livro")
        print("2 - Cadastrar usuário")
        print("3 - Listar livros e disponibilidade")
        print("4 - Listar usuários")
        print("5 - Registrar empréstimo")
        print("6 - Registrar devolução")
        print("0 - Sair")
        opcao = input("Escolha uma opção: ").strip()

        if opcao == "1":
            cadastrar_livro(dados)
        elif opcao == "2":
            cadastrar_usuario(dados)
        elif opcao == "3":
            listar_livros(dados)
        elif opcao == "4":
            listar_usuarios(dados)
        elif opcao == "5":
            registrar_emprestimo(dados)
        elif opcao == "6":
            registrar_devolucao(dados)
        elif opcao == "0":
            print("Sistema encerrado.")
            break
        else:
            print("Opção inválida. Tente novamente.")


if __name__ == "__main__":
    menu()
