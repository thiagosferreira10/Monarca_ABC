from firebird.driver import DatabaseError

def check_and_update_schema(conn):
    """
    Checks if the necessary tables and columns exist in the database.
    If not, it creates them.
    """
    cursor = conn.cursor()
    
    # 1. Check/Create SUGESTAO_NIVEL
    try:
        cursor.execute("SELECT COUNT(*) FROM SUGESTAO_NIVEL")
    except DatabaseError:
        # Table likely doesn't exist
        print("Schema: Creating table SUGESTAO_NIVEL...")
        conn.commit() # Clear transaction state
        create_sql = """
        CREATE TABLE SUGESTAO_NIVEL (
            CODIGO INTEGER NOT NULL PRIMARY KEY,
            NIVEL1 INTEGER,
            NIVEL2 INTEGER,
            NIVEL3 INTEGER,
            NIVEL4 INTEGER,
            ABC    INTEGER,
            MINIMO DECIMAL(18, 2),
            MAXIMO DECIMAL(18, 2)
        )
        """
        cursor.execute(create_sql)
        conn.commit()

    # 2. Check/UPDATE PRODUTOS (MEDIA and ABC)
    # We check by trying to select the column. If fail, we add it.
    
    # Column: MEDIA
    try:
        cursor.execute("SELECT FIRST 1 MEDIA FROM PRODUTOS")
    except DatabaseError:
        print("Schema: Adding column MEDIA to PRODUTOS...")
        conn.commit()
        cursor.execute("ALTER TABLE PRODUTOS ADD MEDIA DECIMAL(18,2)")
        conn.commit()

    # Column: ABC (Classification 1,2,3)
    try:
        cursor.execute("SELECT FIRST 1 ABC FROM PRODUTOS")
    except DatabaseError:
        print("Schema: Adding column ABC to PRODUTOS...")
        conn.commit()
        cursor.execute("ALTER TABLE PRODUTOS ADD ABC INTEGER")
        conn.commit()

    # 3. Check/UPDATE PRODUTOS_NIVEL1 (ABC Flag and Processing Date)
    
    # Column: ABC (String/Char 'S'/'N') - Used for filtering execution
    try:
        cursor.execute("SELECT FIRST 1 ABC FROM PRODUTOS_NIVEL1")
    except DatabaseError:
        print("Schema: Adding column ABC to PRODUTOS_NIVEL1...")
        conn.commit()
        cursor.execute("ALTER TABLE PRODUTOS_NIVEL1 ADD ABC CHAR(1) DEFAULT 'N'")
        conn.commit()

    # Column: DATA_PROCESSAMENTO
    try:
        cursor.execute("SELECT FIRST 1 DATA_PROCESSAMENTO FROM PRODUTOS_NIVEL1")
    except DatabaseError:
        print("Schema: Adding column DATA_PROCESSAMENTO to PRODUTOS_NIVEL1...")
        conn.commit()
        cursor.execute("ALTER TABLE PRODUTOS_NIVEL1 ADD DATA_PROCESSAMENTO TIMESTAMP")
        conn.commit()
        
    # Column: PERCENTUAL (For ABC Share)
    try:
        cursor.execute("SELECT FIRST 1 PERCENTUAL FROM PRODUTOS")
    except DatabaseError:
        print("Schema: Adding column PERCENTUAL to PRODUTOS...")
        conn.commit()
        cursor.execute("ALTER TABLE PRODUTOS ADD PERCENTUAL DECIMAL(18,2)")
        conn.commit()

    # Column: TIPO_PROCESSAMENTO (V=Venda, P=Pedido) for Product Level 1
    try:
        cursor.execute("SELECT FIRST 1 TIPO_PROCESSAMENTO FROM PRODUTOS_NIVEL1")
    except DatabaseError:
        print("Schema: Adding column TIPO_PROCESSAMENTO to PRODUTOS_NIVEL1...")
        conn.commit()
        cursor.execute("ALTER TABLE PRODUTOS_NIVEL1 ADD TIPO_PROCESSAMENTO VARCHAR(1) DEFAULT 'V'")
        conn.commit()
        # Update existing records to default 'V'
        cursor.execute("UPDATE PRODUTOS_NIVEL1 SET TIPO_PROCESSAMENTO = 'V' WHERE TIPO_PROCESSAMENTO IS NULL")
        conn.commit()

    # Column: MESES (Integer) for Product Level 1
    try:
        cursor.execute("SELECT FIRST 1 MESES FROM PRODUTOS_NIVEL1")
    except DatabaseError:
        print("Schema: Adding column MESES to PRODUTOS_NIVEL1...")
        conn.commit()
        cursor.execute("ALTER TABLE PRODUTOS_NIVEL1 ADD MESES INTEGER DEFAULT 24")
        conn.commit()
        # Update existing records to default 24
        cursor.execute("UPDATE PRODUTOS_NIVEL1 SET MESES = 24 WHERE MESES IS NULL")
        conn.commit()

    # Column: ABC (Char 'S'/'N') for Product Level 2
    try:
        cursor.execute("SELECT FIRST 1 ABC FROM PRODUTOS_NIVEL2")
    except DatabaseError:
        print("Schema: Adding column ABC to PRODUTOS_NIVEL2...")
        conn.commit()
        cursor.execute("ALTER TABLE PRODUTOS_NIVEL2 ADD ABC CHAR(1) DEFAULT 'S'")
        conn.commit()
        # Update existing records to default 'S'
        cursor.execute("UPDATE PRODUTOS_NIVEL2 SET ABC = 'S' WHERE ABC IS NULL")
        conn.commit()

    # 8. Check/Create FERRAMENTAS (Access Control - Modules)
    try:
        cursor.execute("SELECT COUNT(*) FROM FERRAMENTAS")
    except DatabaseError:
        print("Schema: Creating table FERRAMENTAS...")
        conn.commit()
        create_sql = """
        CREATE TABLE FERRAMENTAS (
            ID        INTEGER NOT NULL PRIMARY KEY,
            MODULO    INTEGER,
            DESCRICAO VARCHAR(100),
            OPCAO     INTEGER
        )
        """
        cursor.execute(create_sql)
        conn.commit()
        # Insert initial data
        cursor.execute("INSERT INTO FERRAMENTAS (ID, MODULO, DESCRICAO, OPCAO) VALUES (1, 1, 'Administracao', 1)")
        cursor.execute("INSERT INTO FERRAMENTAS (ID, MODULO, DESCRICAO, OPCAO) VALUES (2, 2, 'Sugestão de Compra - Aba1', 1)")
        cursor.execute("INSERT INTO FERRAMENTAS (ID, MODULO, DESCRICAO, OPCAO) VALUES (3, 2, 'Sugestão de Compra - Aba2', 2)")
        conn.commit()
        print("Schema: FERRAMENTAS created with initial data.")

    # 8b. Ensure FERRAMENTAS IDs 4 and 5 exist (tab-level permissions)
    try:
        cursor.execute("SELECT COUNT(*) FROM FERRAMENTAS WHERE ID = 4")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO FERRAMENTAS (ID, MODULO, DESCRICAO, OPCAO) VALUES (4, 2, 'Sugestão de Compra', 1)")
            conn.commit()
            print("Schema: Added FERRAMENTAS ID=4 (Sugestão de Compra)")
        cursor.execute("SELECT COUNT(*) FROM FERRAMENTAS WHERE ID = 5")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO FERRAMENTAS (ID, MODULO, DESCRICAO, OPCAO) VALUES (5, 2, 'Configuração', 2)")
            conn.commit()
            print("Schema: Added FERRAMENTAS ID=5 (Configuração)")
    except DatabaseError:
        conn.commit()

    # 9. Check/Create FERRAMENTAS_PERMISSAO (Access Control - Permissions)
    try:
        cursor.execute("SELECT COUNT(*) FROM FERRAMENTAS_PERMISSAO")
    except DatabaseError:
        print("Schema: Creating table FERRAMENTAS_PERMISSAO...")
        conn.commit()
        create_sql = """
        CREATE TABLE FERRAMENTAS_PERMISSAO (
            FERRAMENTAS  INTEGER,
            USUARIO      INTEGER
        )
        """
        cursor.execute(create_sql)
        conn.commit()
        print("Schema: FERRAMENTAS_PERMISSAO created.")
        
    # 10. Check/Create SUGESTAO_FORNECEDOR
    try:
        cursor.execute("SELECT COUNT(*) FROM SUGESTAO_FORNECEDOR")
    except DatabaseError:
        print("Schema: Creating table SUGESTAO_FORNECEDOR...")
        conn.commit()
        create_sql = """
        CREATE TABLE SUGESTAO_FORNECEDOR (
            CODIGO     INTEGER NOT NULL PRIMARY KEY,
            FORNECEDOR INTEGER,
            TIPO       INTEGER,
            PRAZO      DECIMAL(18, 1)
        )
        """
        cursor.execute(create_sql)
        conn.commit()
        print("Schema: SUGESTAO_FORNECEDOR created.")

    # 10b. Ensure FERRAMENTAS ID=6 exists (Fornecedores tab permission)
    try:
        cursor.execute("SELECT COUNT(*) FROM FERRAMENTAS WHERE ID = 6")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO FERRAMENTAS (ID, MODULO, DESCRICAO, OPCAO) VALUES (6, 2, 'Fornecedores', 3)")
            conn.commit()
            print("Schema: Added FERRAMENTAS ID=6 (Fornecedores)")
    except DatabaseError:
        conn.commit()

    # 11. Check/Create SUGESTAO_DOLAR
    try:
        cursor.execute("SELECT COUNT(*) FROM SUGESTAO_DOLAR")
    except DatabaseError:
        print("Schema: Creating table SUGESTAO_DOLAR...")
        conn.commit()
        create_sql = """
        CREATE TABLE SUGESTAO_DOLAR (
            CODIGO  INTEGER NOT NULL PRIMARY KEY,
            PRODUTO INTEGER,
            DOLAR   DECIMAL(18, 2)
        )
        """
        cursor.execute(create_sql)
        conn.commit()
        print("Schema: SUGESTAO_DOLAR created.")

    # 11b. Ensure FERRAMENTAS ID=7 exists (Produtos Dolar tab permission)
    try:
        cursor.execute("SELECT COUNT(*) FROM FERRAMENTAS WHERE ID = 7")
        if cursor.fetchone()[0] == 0:
            cursor.execute("INSERT INTO FERRAMENTAS (ID, MODULO, DESCRICAO, OPCAO) VALUES (7, 2, 'Produtos Dolar', 4)")
            conn.commit()
            print("Schema: Added FERRAMENTAS ID=7 (Produtos Dolar)")
    except DatabaseError:
        conn.commit()

    print("Schema Check Completed.")
