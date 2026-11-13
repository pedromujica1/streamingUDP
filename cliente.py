#TRECHOS uteis
#vai precisar usar isso
# cv2.imshow("Top Video",frame)
'''

#se pressiona a tecla q, destroi janela
    if 0xFF == ord('q'):
        break
'''

'''
Seguindo a arquitetura definida nas Seções 4, 5 e 6 do seu documento de projeto, a lógica do `cliente.py` se divide em quatro etapas diretas:

1. **Inicialização e Conexão (`JOIN`)**
* Lê os argumentos via `argparse`: endereço IP e porta do servidor, além do timeout para descartar frames incompletos.


* Abre um socket UDP (`SOCK_DGRAM`), aumenta o buffer de recepção (`SO_RCVBUF`) para evitar perdas em rajadas e envia um pacote `JOIN` (com os demais campos zerados) para o servidor.


* Inicia duas threads secundárias (`daemon=True`) e uma `Queue` compartilhada.




2. **Thread de Keep-Alive**
* Roda em loop dormindo um intervalo fixo (ex: a cada 2 ou 3 segundos, bem menor que os 7s de timeout do seu servidor) e envia um pacote `KEEPALIVE` para manter o cadastro ativo no servidor.




3. **Thread de Recepção e Remontagem**
* Fica em `recvfrom()` lendo os datagramas com `ler_pacote()` e gerenciando um dicionário de remontagem indexado por `frame_id`:


* **Descarte de atrasados:** Ignora qualquer pacote cujo `frame_id` seja menor ou igual ao do último frame já exibido.


* **Armazenamento:** Salva o payload na posição `frag_idx` (ignorando duplicatas) e registra o instante de chegada do primeiro pedaço daquele frame.


* **Frame completo:** Quando a quantidade de pedaços atingir `total_frags`, junta os bytes na ordem (`0` até `total_frags - 1`), coloca o frame pronto e seu `timestamp` na `Queue` de exibição, e apaga do dicionário todos os frames incompletos mais antigos (`frame_id` menor).


* **Limpeza por timeout:** Remove frames incompletos que ultrapassaram o tempo limite configurado ou o limite máximo de frames simultâneos no buffer (ex: 5).






4. **Thread Principal: Exibição e Encerramento (`EXIT`)**
* Pega os bytes JPEG prontos da `Queue`, converte em matriz com `np.frombuffer` + `cv2.imdecode`, calcula a latência (`agora_us() - timestamp`) para as métricas e atualiza a janela com `cv2.imshow`. (Se nenhum frame novo chegar, mantém o último frame exibido sem piscar tela preta).


* Ao pressionar `'q'` ou fechar com `Ctrl+C`, envia um pacote `EXIT` ao servidor, fecha a janela e encerra o socket.'''



