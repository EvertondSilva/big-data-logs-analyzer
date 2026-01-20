import dash
from dash import dcc, html, Input, Output
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import os

# Carregar variáveis de ambiente
load_dotenv()

# Configurações do PostgreSQL
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'nasa_logs_db')
DB_USER = os.getenv('DB_USER', 'nasa_user')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'nasa_password')

# Criar engine SQLAlchemy
DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
engine = create_engine(DATABASE_URL)

print(f"🔗 Conectando em: postgresql://{DB_USER}:***@{DB_HOST}:{DB_PORT}/{DB_NAME}")

# Função para carregar dados
def load_data_from_db(query):
    """Carrega dados do PostgreSQL usando SQLAlchemy"""
    try:
        with engine.connect() as conn:
            df = pd.read_sql_query(text(query), conn)
        return df
    except Exception as e:
        print(f"❌ Erro ao executar query: {str(e)}")
        return pd.DataFrame()

# Carregar dados das análises
def load_dashboard_data():
    """Carrega todos os dados necessários para o dashboard"""
    
    print("📥 Carregando dados do banco...")
    data = {}
    
    # 1. Estatísticas gerais
    query_stats = """
        SELECT 
            COUNT(*) as total_logs,
            COUNT(DISTINCT ip) as unique_ips,
            SUM(bytes) as total_bytes,
            AVG(bytes) as avg_bytes
        FROM logs
    """
    data['stats'] = load_data_from_db(query_stats)
    if not data['stats'].empty:
        print(f"✅ Estatísticas gerais carregadas: {data['stats'].iloc[0]['total_logs']:,} logs")
    else:
        print("⚠️ Nenhuma estatística encontrada")
    
    # 2. Top IPs
    try:
        data['top_ips'] = load_data_from_db("SELECT * FROM analysis_suspicious_ips ORDER BY request_count DESC LIMIT 20")
        print(f"✅ Top IPs: {len(data['top_ips'])} registros")
    except Exception as e:
        print(f"⚠️ Tabela analysis_suspicious_ips não encontrada: {e}")
        # Fallback: calcular diretamente
        query_fallback = """
            SELECT ip, COUNT(*) as requests, SUM(bytes) as total_bytes, AVG(bytes) as avg_bytes
            FROM logs
            GROUP BY ip
            ORDER BY requests DESC
            LIMIT 20
        """
        data['top_ips'] = load_data_from_db(query_fallback)
        print(f"✅ Top IPs (fallback): {len(data['top_ips'])} registros")
    
    # 3. Top Recursos
    try:
        data['top_resources'] = load_data_from_db("SELECT url, COUNT(*) AS total_acessos, COUNT(bytes) AS total_bytes FROM logs GROUP BY url ORDER BY total_acessos desc LIMIT 20;")
        print(f"✅ Top Recursos: {len(data['top_resources'])} registros")
    except Exception as e:
        print(f"⚠️ Tabela analysis_top_resources não encontrada: {e}")
        query_fallback = """
            SELECT url, COUNT(*) as requests, SUM(bytes) as total_bytes
            FROM logs
            GROUP BY url
            ORDER BY requests DESC
            LIMIT 20
        """
        data['top_resources'] = load_data_from_db(query_fallback)
        print(f"✅ Top Recursos (fallback): {len(data['top_resources'])} registros")
    
    # 4. Métodos HTTP
    try:
        data['http_methods'] = load_data_from_db("SELECT * FROM analysis_http_methods ORDER BY count DESC")
        print(f"✅ Métodos HTTP: {len(data['http_methods'])} registros")
    except Exception as e:
        print(f"⚠️ Tabela analysis_http_methods não encontrada: {e}")
        query_fallback = """
            SELECT method, COUNT(*) as count
            FROM logs
            GROUP BY method
            ORDER BY count DESC
        """
        data['http_methods'] = load_data_from_db(query_fallback)
        print(f"✅ Métodos HTTP (fallback): {len(data['http_methods'])} registros")
    
    # 5. IPs Suspeitos
    try:
        data['suspicious_ips'] = load_data_from_db("SELECT * FROM analysis_suspicious_ips ORDER BY request_count DESC LIMIT 20")
        print(f"✅ IPs Suspeitos: {len(data['suspicious_ips'])} registros")
    except Exception as e:
        print(f"⚠️ Tabela analysis_suspicious_ips não encontrada: {e}")
        data['suspicious_ips'] = pd.DataFrame()
    
    # 6. Distribuição de códigos de status
    query_status = """
        SELECT response, COUNT(*) as count
        FROM logs
        GROUP BY response
        ORDER BY count DESC
        LIMIT 10
    """
    data['status_codes'] = load_data_from_db(query_status)
    print(f"✅ Status Codes: {len(data['status_codes'])} registros")
    
    print("✅ Todos os dados carregados!\n")
    return data

# Inicializar o app Dash
app = dash.Dash(__name__, suppress_callback_exceptions=True)
app.title = "NASA Logs Dashboard"

# Carregar dados iniciais
print("\n" + "="*60)
print("🚀 INICIALIZANDO DASHBOARD")
print("="*60)
dashboard_data = load_dashboard_data()

# Layout do Dashboard

app.layout = html.Div([
    # Header
    html.Div([
        html.H1("🚀 NASA Access Logs - Analytics Dashboard", 
                style={'textAlign': 'center', 'color': '#ffffff', 'marginBottom': '10px'}),
        html.P("Análise de Logs de Acesso da NASA (Julho 1995)", 
               style={'textAlign': 'center', 'color': '#cccccc', 'fontSize': '18px'}),
    ], style={'backgroundColor': '#1e3a8a', 'padding': '20px', 'marginBottom': '20px'}),
    
    # Botão de atualização
    html.Div([
        html.Button('🔄 Atualizar Dados', id='refresh-button', n_clicks=0,
                   style={'backgroundColor': '#3b82f6', 'color': 'white', 'padding': '10px 20px', 
                          'border': 'none', 'borderRadius': '5px', 'cursor': 'pointer', 
                          'fontSize': '16px', 'fontWeight': 'bold'})
    ], style={'textAlign': 'center', 'marginBottom': '20px'}),
    
    # KPIs - Cards em Grid 4 colunas
    html.Div([
        # Card 1: Total de Logs
        html.Div([
            html.H3("📊 Total de Logs", style={'fontSize': '16px', 'marginBottom': '10px'}),
            html.H2(id='kpi-total-logs', style={'color': '#3b82f6', 'fontSize': '28px', 'margin': '0'})
        ], style={'backgroundColor': '#f0f9ff', 'padding': '20px', 'borderRadius': '10px', 
                  'textAlign': 'center', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
        
        # Card 2: IPs Únicos
        html.Div([
            html.H3("🌐 IPs Únicos", style={'fontSize': '16px', 'marginBottom': '10px'}),
            html.H2(id='kpi-unique-ips', style={'color': '#10b981', 'fontSize': '28px', 'margin': '0'})
        ], style={'backgroundColor': '#f0fdf4', 'padding': '20px', 'borderRadius': '10px', 
                  'textAlign': 'center', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
        
        # Card 3: Total de Bytes
        html.Div([
            html.H3("💾 Total de Bytes", style={'fontSize': '16px', 'marginBottom': '10px'}),
            html.H2(id='kpi-total-bytes', style={'color': '#f59e0b', 'fontSize': '28px', 'margin': '0'})
        ], style={'backgroundColor': '#fffbeb', 'padding': '20px', 'borderRadius': '10px', 
                  'textAlign': 'center', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
        
        # Card 4: Bytes Médios
        html.Div([
            html.H3("📈 Bytes Médios", style={'fontSize': '16px', 'marginBottom': '10px'}),
            html.H2(id='kpi-avg-bytes', style={'color': '#8b5cf6', 'fontSize': '28px', 'margin': '0'})
        ], style={'backgroundColor': '#faf5ff', 'padding': '20px', 'borderRadius': '10px', 
                  'textAlign': 'center', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
    ], style={'display': 'grid', 'gridTemplateColumns': 'repeat(auto-fit, minmax(250px, 1fr))', 
              'gap': '20px', 'marginBottom': '30px', 'padding': '0 20px'}),
    
    html.Div([
            # Top 20 IPs - Tabela
            html.Div([
                html.H3("🌐 Top 20 IPs Mais Ativos", 
                    style={'textAlign': 'center', 'color': '#1e3a8a', 'marginBottom': '15px'}),
                html.Div(id='table-top-ips', style={'overflowY': 'auto', 'maxHeight': '600px'})
            ], style={'flex': '1', 'minWidth': '500px', 'backgroundColor': 'white', 
                    'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
            
            # Top 20 Recursos - Tabela
            html.Div([
                html.H3("📂 Top 20 Recursos Mais Acessados", 
                    style={'textAlign': 'center', 'color': '#1e3a8a', 'marginBottom': '15px'}),
                html.Div(id='table-top-resources', style={'overflowY': 'auto', 'maxHeight': '600px'})
            ], style={'flex': '1', 'minWidth': '500px', 'backgroundColor': 'white', 
                    'padding': '20px', 'borderRadius': '10px', 'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'}),
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'padding': '0 20px', 'marginBottom': '20px'}),
        
        # Gráficos - Linha 2 (Grid 2 colunas)
        html.Div([
            html.Div([
                dcc.Graph(id='chart-http-methods', style={'height': '500px'})
            ], style={'flex': '1', 'minWidth': '500px'}),
            
            html.Div([
                dcc.Graph(id='chart-status-codes', style={'height': '500px'})
            ], style={'flex': '1', 'minWidth': '500px'}),
        ], style={'display': 'flex', 'flexWrap': 'wrap', 'gap': '20px', 'padding': '0 20px', 'marginBottom': '30px'}),
        
        # IPs Suspeitos - Tabela
        html.Div([
            html.H2("🚨 IPs Suspeitos Detectados", 
                    style={'textAlign': 'center', 'marginTop': '30px', 'marginBottom': '20px', 'color': '#1e3a8a'}),
            html.Div(id='table-suspicious-ips', style={'padding': '0 20px'})
        ]),
        
        # Store para dados
        dcc.Store(id='dashboard-data')
        
    ], style={'backgroundColor': '#f9fafb', 'minHeight': '100vh', 'paddingBottom': '50px', 'fontFamily': 'Arial, sans-serif'})
# Callbacks
@app.callback(
    [Output('kpi-total-logs', 'children'),
     Output('kpi-unique-ips', 'children'),
     Output('kpi-total-bytes', 'children'),
     Output('kpi-avg-bytes', 'children'),
     Output('table-top-ips', 'children'),
     Output('table-top-resources', 'children'),
     Output('chart-http-methods', 'figure'),
     Output('chart-status-codes', 'figure'),
     Output('table-suspicious-ips', 'children')],
    [Input('refresh-button', 'n_clicks')]
)
def update_dashboard(n_clicks):
    """Atualiza todo o dashboard"""
    
    print(f"\n🔄 Atualizando dashboard (click #{n_clicks})...")
    
    # Recarregar dados
    data = load_dashboard_data()
    
    # KPIs
    if not data['stats'].empty:
        stats = data['stats'].iloc[0]
        total_logs = f"{int(stats['total_logs']):,}"
        unique_ips = f"{int(stats['unique_ips']):,}"
        total_bytes_gb = stats['total_bytes'] / (1024**3) if stats['total_bytes'] else 0
        total_bytes = f"{total_bytes_gb:.2f} GB"
        avg_bytes_kb = stats['avg_bytes'] / 1024 if stats['avg_bytes'] else 0
        avg_bytes = f"{avg_bytes_kb:.2f} KB"
    else:
        total_logs = "N/A"
        unique_ips = "N/A"
        total_bytes = "N/A"
        avg_bytes = "N/A"
    
    # Tabela 1: Top 20 IPs
    if not data['top_ips'].empty:
        table_header_ips = html.Thead(html.Tr([
            html.Th("#", style={'padding': '12px', 'backgroundColor': '#3b82f6', 'color': 'white', 
                                'position': 'sticky', 'top': '0', 'zIndex': '10', 'width': '50px'}),
            html.Th("IP", style={'padding': '12px', 'backgroundColor': '#3b82f6', 'color': 'white', 
                                'position': 'sticky', 'top': '0', 'zIndex': '10'}),
            html.Th("Requests", style={'padding': '12px', 'backgroundColor': '#3b82f6', 'color': 'white', 
                                    'textAlign': 'right', 'position': 'sticky', 'top': '0', 'zIndex': '10'}),
            html.Th("Total Bytes", style={'padding': '12px', 'backgroundColor': '#3b82f6', 'color': 'white', 
                                        'textAlign': 'right', 'position': 'sticky', 'top': '0', 'zIndex': '10'}),
        ]))
        
        rows_ips = []
        for idx, row in data['top_ips'].head(20).iterrows():
            # Cores alternadas
            bg_color = '#f0f9ff' if idx % 2 == 0 else 'white'
            rows_ips.append(html.Tr([
                html.Td(f"{idx + 1}", style={'padding': '12px', 'fontWeight': 'bold', 
                                            'color': '#3b82f6', 'backgroundColor': bg_color, 
                                            'textAlign': 'center'}),
                html.Td(row['ip'], style={'padding': '12px', 'fontFamily': 'monospace', 
                                        'backgroundColor': bg_color}),
                html.Td(f"{int(row['request_count']):,}", style={'padding': '12px', 'textAlign': 'right', 
                                                                'fontWeight': 'bold', 'backgroundColor': bg_color}),
                html.Td(f"{int(row['avg_bytes']) / (1024**2):.2f} MB", 
                    style={'padding': '12px', 'textAlign': 'right', 'backgroundColor': bg_color}),
            ]))
        
        table_body_ips = html.Tbody(rows_ips)
        table_ips = html.Table(
            [table_header_ips, table_body_ips],
            style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '14px'}
        )
    else:
        table_ips = html.Div("❌ Dados não disponíveis", 
                            style={'textAlign': 'center', 'padding': '20px', 'color': '#999'})
    
   # Tabela 2: Top 20 Recursos
    if not data['top_resources'].empty:
        table_header_resources = html.Thead(html.Tr([
            html.Th("#", style={'padding': '12px', 'backgroundColor': '#10b981', 'color': 'white', 
                                'position': 'sticky', 'top': '0', 'zIndex': '10', 
                                'width': '50px', 'textAlign': 'center'}),
            html.Th("Recurso (URL)", style={'padding': '12px', 'backgroundColor': '#10b981', 'color': 'white', 
                                            'position': 'sticky', 'top': '0', 'zIndex': '10',
                                            'width': '50%'}),
            html.Th("Requests", style={'padding': '12px', 'backgroundColor': '#10b981', 'color': 'white', 
                                    'textAlign': 'right', 'position': 'sticky', 'top': '0', 'zIndex': '10',
                                    'width': '120px'}),
            html.Th("Total Bytes", style={'padding': '12px', 'backgroundColor': '#10b981', 'color': 'white', 
                                        'textAlign': 'right', 'position': 'sticky', 'top': '0', 'zIndex': '10',
                                        'width': '120px'}),
        ]))
        
        rows_resources = []
        for idx, row in data['top_resources'].head(20).iterrows():
            bg_color = '#f0fdf4' if idx % 2 == 0 else 'white'
            # Truncar URL para exibição
            url_display = str(row['url'])[:60] + '...' if len(str(row['url'])) > 60 else str(row['url'])
            
            rows_resources.append(html.Tr([
                html.Td(f"{idx + 1}", style={'padding': '12px', 'fontWeight': 'bold', 
                                            'color': '#10b981', 'backgroundColor': bg_color,
                                            'textAlign': 'center', 'width': '50px'}),
                html.Td(url_display, style={'padding': '12px', 'fontFamily': 'monospace', 
                                            'fontSize': '12px', 'backgroundColor': bg_color,
                                            'maxWidth': '400px', 'overflow': 'hidden', 
                                            'textOverflow': 'ellipsis', 'whiteSpace': 'nowrap',
                                            'width': '50%'},
                    title=str(row['url'])),  # Tooltip com URL completo
                html.Td(f"{int(row['total_acessos']):,}", style={'padding': '12px', 'textAlign': 'right', 
                                                                'fontWeight': 'bold', 'backgroundColor': bg_color,
                                                                'width': '120px'}),
                html.Td(f"{int(row['total_bytes']) / (1024**2):.2f} MB", 
                    style={'padding': '12px', 'textAlign': 'right', 'backgroundColor': bg_color,
                            'width': '120px'}),
            ]))
        
        table_body_resources = html.Tbody(rows_resources)
        table_resources = html.Table(
            [table_header_resources, table_body_resources],
            style={'width': '100%', 'borderCollapse': 'collapse', 'fontSize': '14px', 'tableLayout': 'fixed'}
        )
    else:
        table_resources = html.Div("❌ Dados não disponíveis", 
                                style={'textAlign': 'center', 'padding': '20px', 'color': '#999'})
    # Gráfico 3: Métodos HTTP
    if not data['http_methods'].empty:
        fig_http_methods = px.pie(
            data['http_methods'],
            values='count',
            names='method',
            title='Distribuição de Métodos HTTP',
            color_discrete_sequence=px.colors.qualitative.Set3
        )
        fig_http_methods.update_traces(textposition='inside', textinfo='percent+label')
        fig_http_methods.update_layout(showlegend=True, legend=dict(orientation="v"))
    else:
        fig_http_methods = go.Figure()
        fig_http_methods.add_annotation(text="❌ Dados não disponíveis", showarrow=False, font=dict(size=20))
        fig_http_methods.update_layout(title='Distribuição de Métodos HTTP')
    
    # Gráfico 4: Status Codes Agrupados por Categoria
    if not data['status_codes'].empty:
        # Filtrar apenas códigos entre 200 e 600
        df_status = data['status_codes'].copy()
        df_status = df_status[(df_status['response'] >= 200) & (df_status['response'] < 600)]
        
        # Função para categorizar
        def get_status_category(code):
            if 200 <= code < 300:
                return '2xx - Sucesso'
            elif 300 <= code < 400:
                return '3xx - Redirecionamento'
            elif 400 <= code < 500:
                return '4xx - Erro do Cliente'
            elif 500 <= code < 600:
                return '5xx - Erro do Servidor'
            else:
                return 'Outros'
        
        # Aplicar categorização
        df_status['category'] = df_status['response'].apply(get_status_category)
        
        # AGRUPAR E SOMAR por categoria
        df_grouped = df_status.groupby('category')['count'].sum().reset_index()
        df_grouped = df_grouped.sort_values('category')
        
        # Mapa de cores
        color_map = {
            '2xx - Sucesso': '#10b981',
            '3xx - Redirecionamento': '#3b82f6',
            '4xx - Erro do Cliente': '#f59e0b',
            '5xx - Erro do Servidor': '#ef4444',
            'Outros': '#6b7280'
        }
        
        # Criar gráfico de barras
        fig_status_codes = go.Figure(data=[
            go.Bar(
                x=df_grouped['category'],
                y=df_grouped['count'],
                marker=dict(
                    color=[color_map.get(cat, '#6b7280') for cat in df_grouped['category']],
                    line=dict(color='#ffffff', width=2)
                ),
                text=df_grouped['count'],
                textposition='outside',
                texttemplate='%{text:,}',
                hovertemplate='<b>%{x}</b><br>Total: %{y:,} requests<extra></extra>'
            )
        ])
        
        fig_status_codes.update_layout(
            title='Distribuição de Status HTTP por Categoria',
            xaxis_title="Categoria de Status",
            yaxis_title="Quantidade Total",
            showlegend=False,
            height=500,
            template='plotly_white',
            xaxis=dict(
                categoryorder='array',
                categoryarray=['2xx - Sucesso', '3xx - Redirecionamento', '4xx - Erro do Cliente', '5xx - Erro do Servidor', 'Outros']
            )
        )
    else:
        fig_status_codes = go.Figure()
        fig_status_codes.add_annotation(text="❌ Dados não disponíveis", showarrow=False, font=dict(size=20))
        fig_status_codes.update_layout(title='Distribuição de Status HTTP por Categoria')
        
    # Tabela: IPs Suspeitos
    if not data['suspicious_ips'].empty:
        table_header_suspicious = html.Thead(html.Tr([
            html.Th("Ranking", style={'padding': '12px', 'backgroundColor': '#ef4444', 'color': 'white'}),
            html.Th("IP", style={'padding': '12px', 'backgroundColor': '#ef4444', 'color': 'white'}),
            html.Th("Requests", style={'padding': '12px', 'backgroundColor': '#ef4444', 'color': 'white', 'textAlign': 'right'}),
            html.Th("Bytes Médios", style={'padding': '12px', 'backgroundColor': '#ef4444', 'color': 'white', 'textAlign': 'right'}),
        ]))
        
        rows_suspicious = []
        for idx, row in data['suspicious_ips'].head(20).iterrows():
            bg_color = '#fef2f2' if idx % 2 == 0 else 'white'
            rows_suspicious.append(html.Tr([
                html.Td(f"#{idx + 1}", style={'padding': '10px', 'fontWeight': 'bold', 
                                               'color': '#ef4444', 'backgroundColor': bg_color}),
                html.Td(row['ip'], style={'padding': '10px', 'fontFamily': 'monospace', 'backgroundColor': bg_color}),
                html.Td(f"{int(row['request_count']):,}", style={'padding': '10px', 'textAlign': 'right', 
                                                                 'fontWeight': 'bold', 'backgroundColor': bg_color}),
                html.Td(f"{row['avg_bytes']:.2f} bytes", style={'padding': '10px', 'textAlign': 'right', 'backgroundColor': bg_color}),
            ]))
        
        table_body_suspicious = html.Tbody(rows_suspicious)
        table_suspicious = html.Table(
            [table_header_suspicious, table_body_suspicious],
            style={'width': '100%', 'borderCollapse': 'collapse', 'backgroundColor': 'white', 
                   'boxShadow': '0 4px 6px rgba(0,0,0,0.1)', 'borderRadius': '10px', 'overflow': 'hidden'}
        )
    else:
        table_suspicious = html.Div("✅ Nenhum IP suspeito detectado", 
                                    style={'textAlign': 'center', 'padding': '20px', 'fontSize': '18px', 
                                           'backgroundColor': 'white', 'borderRadius': '10px', 
                                           'boxShadow': '0 4px 6px rgba(0,0,0,0.1)'})
    
    print("✅ Dashboard atualizado com sucesso!\n")
    
    return (total_logs, unique_ips, total_bytes, avg_bytes, 
            table_ips, table_resources, fig_http_methods, fig_status_codes, table_suspicious)

# Executar o servidor
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🚀 DASHBOARD PRONTO!")
    print("="*60)
    print("📊 Acesse: http://localhost:8050")
    print("="*60 + "\n")
    app.run_server(debug=True, host='0.0.0.0', port=8050)