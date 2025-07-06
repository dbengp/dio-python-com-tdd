# dio-python-com-tdd
Criando Uma API Com FastAPI Utilizando TDD

### Esse projeto tem o intuito de concluir o desafio proposto no bootcamp Santander 2025 - Back-End com Python, a base dele foi cosntruida sob orientação de https://github.com/nayannanara em stream da DIO. Veja o projeto original em https://github.com/digitalinnovationone/store_api

### A conclusão das tarefas abaixo consolida o desafio porposta pela instrutora:
- Create:
    * Mapear uma exceção, caso dê algum erro de inserção e capturar na controller
- Update:
    * Modifique o método de patch para retornar uma exceção de Not Found, quando o dado não for encontrado
    * a exceção deve ser tratada na controller, pra ser retornada uma mensagem amigável pro usuário
    * ao alterar um dado, a data de updated_at deve corresponder ao time atual, permitir modificar updated_at também
- Filtros:
    * cadastre produtos com preços diferentes
    * aplique um filtro de preço, assim: (price > 5000 and price < 8000)
