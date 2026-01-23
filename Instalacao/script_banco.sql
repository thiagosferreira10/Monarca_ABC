/* Script de Configuração do Banco de Dados - Sistema Monarca Curva ABC */

/* 1. Tabela para armazenar as regras de sugestão de compra */
CREATE TABLE SUGESTAO_NIVEL (
    CODIGO INTEGER NOT NULL PRIMARY KEY,
    NIVEL1 INTEGER,
    NIVEL2 INTEGER,
    NIVEL3 INTEGER,
    NIVEL4 INTEGER,
    ABC    INTEGER,
    MINIMO DECIMAL(18, 2),
    MAXIMO DECIMAL(18, 2)
);

/* 2. Atualizações na Tabela PRODUTOS (caso não existam) */
/* O sistema utiliza os campos ABC (Integer) e MEDIA (Decimal) na tabela PRODUTOS.
   Certifique-se de que eles existem. */
/* ALTER TABLE PRODUTOS ADD MEDIA DECIMAL(18,2); */
/* ALTER TABLE PRODUTOS ADD ABC INTEGER; */

/* 3. Atualizações na Tabela PRODUTOS_NIVEL1 */
/* O sistema utiliza DATA_PROCESSAMENTO para controle */
/* ALTER TABLE PRODUTOS_NIVEL1 ADD DATA_PROCESSAMENTO TIMESTAMP; */

/* Fim do Script */
