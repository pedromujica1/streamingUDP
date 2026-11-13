# streamingUDP
Trabalho de Redes de aplicação para Streaming em UDP


## Configuração do Ambiente

### 1. Criar e ativar o ambiente virtual (venv)

* **Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate

* **Windows (PowerShell):**


  ```powershell
  python -m venv venv
  .\venv\Scripts\Activate.ps1

  ```

---

### 2. Instalar as dependências

Com o ambiente virtual ativado, execute:

```bash
pip install -r requirements.txt

```

---

## 3. Como Executar

Para iniciar o sistema especialista:

* **Interface Web:**
```bash
python app.py

```
Depois é só abrir http://localhost:5000 no navegador. O seletor "Carregar exemplo" preenche o formulário com os mesmos pedidos do modo demonstração.

* **Menu Interativo (terminal):**
```bash
python main.py

```

* **Rodar Pedidos de Exemplo (modo demonstração):**
```bash
python main.py --demo

```

