DATABASE_VALIDATIONS = [
    {
        "name": "STEP 1 - Report",
        "description": "Validação para garantir que as carga tenha chegado na tabela.",
        "query": """
            SELECT
                IIF(SUM(Column) > 1, 'TRUE', 'FALSE') Status,
                Last_Date_Available AS Last_Date,
                SUM(Column) AS Daily_Quantity,
                COUNT(Column) AS Total_Quantity
            FROM RankedOpportunities
            GROUP BY Last_Date_Available
            ORDER BY Last_Date_Available desc;
        """,
        "status_check_column": "Status",
        "multi_row": True
    },
    # Adicione mais validações aqui, se necessário
]