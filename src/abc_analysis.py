import pandas as pd

def process_abc_curve(df, metric_column='VALOR_TOTAL'):
    """
    Processes the ABC curve based on the provided DataFrame.
    Expected columns: CODIGO, REFERENCIA, DESCRICAO, QUANTIDADE_TOTAL, VALOR_TOTAL
    metric_column: 'VALOR_TOTAL' or 'QUANTIDADE_TOTAL'
    """
    if df.empty:
        return df

    # Calculate Total Share
    total_metric = df[metric_column].sum()
    
    if total_metric == 0:
        df['VALOR_ACUMULADO'] = 0.0
        df['PERCENTUAL_ACUMULADO'] = 0.0
        df['PERCENTUAL'] = 0.0
        df['CLASSE'] = 'C' # Default to C if no value
        return df
    
    # Sort by Metric (Pareto Principle: High value items first)
    df = df.sort_values(by=metric_column, ascending=False).reset_index(drop=True)
    
    # Cumulative Sum
    df['VALOR_ACUMULADO'] = df[metric_column].cumsum()
    
    # Cumulative Percentage
    df['PERCENTUAL_ACUMULADO'] = (df['VALOR_ACUMULADO'] / total_metric) * 100
    
    # Individual Percentage
    df['PERCENTUAL'] = (df[metric_column] / total_metric) * 100
    
    # Classification Logic
    def classify(pct):
        if pct <= 80:
            return 'A'
        elif pct <= 95:
            return 'B'
        else:
            return 'C'
            
    df['CLASSE'] = df['PERCENTUAL_ACUMULADO'].apply(classify)
    
    return df
