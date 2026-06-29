# Swavy Finance 🚀

O **Swavy Finance** é um ecossistema web de gestão financeira pessoal de alta fidelidade focado em experiência do usuário (UX) e precisão contábil. A plataforma centraliza o controle de ativos, contas correntes, investimentos e cartões de crédito em uma interface responsiva otimizada para o modo escuro (*Dark Mode*). 

Diferente de planilhas estáticas, o sistema calcula saldos dinamicamente integrando logs de transações e automações inteligentes, oferecendo uma visibilidade preditiva real do fluxo de caixa e planejamento de patrimônio.

---

## 🛠️ Tecnologias e Ferramentas

O projeto foi construído utilizando uma arquitetura robusta dividida entre um back-end altamente tipado para regras de negócio e um front-end dinâmico e leve:

- **Back-end:** [Python](https://www.python.org/) com o micro-framework [Flask](https://flask.palletsprojects.com/) estruturado em *Blueprints* para modularização de rotas.
- **Front-end:** [HTML5](https://developer.mozilla.org/pt-BR/docs/Web/HTML), [Tailwind CSS / Bootstrap 5](https://getbootstrap.com/) para design de componentes atômicos e [JavaScript (Vanilla)](https://developer.mozilla.org/pt-BR/docs/Web/JavaScript) para manipulação assíncrona do DOM.
- **Motor de Template:** [Jinja2](https://jinja.palletsprojects.com/) para renderização dinâmica de dados do servidor diretamente na interface de usuário.
- **Banco de Dados Relacional:** [PostgreSQL](https://www.postgresql.org/) para persistência de dados blindada com suporte nativo a transações complexas e consultas analíticas de tempo (EXTRACT/DATE).

---

## 🔥 Funcionalidades Principais

- **Dashboard Holístico:** Sumarização inteligente em tempo real dividida em blocos de liquidez (Disponível, Guardado, Fatura Atual e cálculo automático do Patrimônio Líquido).
- **Máquina do Tempo (Navegação Mensal):** Sistema de navegação por parâmetros (`?mes=&ano=`) acoplado ao banco de dados, permitindo inspecionar extratos e balanços de meses passados ou planejar lançamentos futuros.
- **Módulo de Faturas Inteligente:** - Termômetro dinâmico de uso de limite com barras de progresso adaptativas por criticidade (Verde/Amarelo/Vermelho).
  - **Lógica de Dia Útil Bancário:** Ajuste automático da data de vencimento da fatura. Caso o dia configurado caia em um sábado ou domingo, a interface empurra o vencimento automaticamente para a próxima segunda-feira útil.
- **Carrossel de Projeções Trimensal:** Visualização em rolagem horizontal dos próximos 3 meses com suporte a **Ajuste de Previsão Manual** (o sistema calcula a diferença e injeta uma transação compensatória no banco para manter o planejamento perfeito).
- **Fluxo de Pagamento Integrado:** Amortização automatizada de faturas atuando como transferência interna, abatendo o saldo de uma conta corrente e zerando a dívida do cartão de forma atômica no banco de dados.
- **UX Dinâmica de Formulários:** Injeção de regras em JavaScript nos formulários de contas para ocultar ou exibir campos específicos (limite de crédito, dia de vencimento) apenas quando o tipo de conta "Cartão de Crédito" estiver ativo.

---

## 🔑 Configuração do Arquivo `.env`

O sistema utiliza variáveis de ambiente para isolar credenciais de segurança e strings de conexão de infraestrutura. Crie um arquivo chamado `.env` na raiz do projeto e configure as seguintes chaves:

```env
# Configurações do Flask
FLASK_APP=app.py
FLASK_DEBUG=1
SECRET_KEY=sua_chave_secreta_aqui_para_criptografia_de_sessoes

# Conexão com o Banco de Dados PostgreSQL
DB_HOST=seu_host_do_banco (Ex: localhost ou endpoint de nuvem)
DB_NAME=nome_do_seu_banco_de_dados
DB_USER=seu_usuario_do_postgres
DB_PASSWORD=sua_senha_do_postgres
DB_PORT=5432

# Integração Open Finance (Opcional se utilizar Sincronização Automática)
PLUGGY_CLIENT_ID=seu_client_id_do_pluggy
PLUGGY_CLIENT_SECRET=seu_client_secret_do_pluggy
