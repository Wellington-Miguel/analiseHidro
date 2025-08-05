import streamlit as st
import pandas as pd
from zipfile import ZipFile
import io

# ============================================================================
# FUNÇÃO FINAL COM A LÓGICA DE TRATAMENTO DE ERROS CORRIGIDA
# ============================================================================
def processar_zip(arquivo_zip_bytes, outorga_diaria_definida):
    resumos = []
    
    # --- NOVA FUNÇÃO AUXILIAR ---
    # Converte horas decimais para o formato de texto HH:MM
    def converter_horas_para_hhmm(horas_decimais):
        if pd.isna(horas_decimais):
            return ""
        horas = int(horas_decimais)
        minutos = int(round((horas_decimais - horas) * 60))
        return f"{horas:02d}:{minutos:02d}"

    try:
        with ZipFile(io.BytesIO(arquivo_zip_bytes), 'r') as zip_ref:
            arquivos_csv = sorted([f for f in zip_ref.namelist() if f.upper().endswith('.CSV')])
            
            if not arquivos_csv:
                st.error("Nenhum arquivo .csv ou .CSV foi encontrado dentro do arquivo ZIP.")
                return None

            for arquivo in arquivos_csv:
                with zip_ref.open(arquivo) as f:
                    df = pd.read_csv(f, encoding='ISO-8859-1', header=None)
                    
                    if df.empty:
                        continue
                        
                    df_filtrado = df.iloc[:, [0, 1, 2, 5]].copy()
                    df_filtrado.columns = ['id', 'data', 'hora', 'vazao_total']
                    
                    df_filtrado['vazao_total'] = pd.to_numeric(df_filtrado['vazao_total'], errors='coerce')
                    df_filtrado.dropna(subset=['vazao_total'], inplace=True)

                    if df_filtrado.empty:
                        continue
                    
                    dif_vazao = df_filtrado['vazao_total'].diff().fillna(0)
                    bombeamentos = (dif_vazao >= 2).sum()
                    
                    resumos.append({
                        'data': df_filtrado['data'].iloc[0],
                        'hora_final': df_filtrado['hora'].iloc[-1],
                        'vazao_total_final': df_filtrado['vazao_total'].iloc[-1],
                        'tempo_total_bombeamento_horas': (bombeamentos * 15) / 60,
                        'vazao_outorgada': outorga_diaria_definida 
                    })

        if not resumos:
            st.error("Processamento concluído, mas nenhum arquivo CSV com dados válidos foi encontrado.")
            return None

        # --- Preparação do DataFrame Final ---
        df_final = pd.DataFrame(resumos)
        df_final['data'] = pd.to_datetime(df_final['data'], errors='coerce', format='%Y/%m/%d')
        
        df_final.dropna(subset=['data'], inplace=True)
        if df_final.empty:
            st.error("Nenhuma data válida foi encontrada. Verifique se os arquivos contêm datas no formato AAAA/MM/DD.")
            return None

        df_final = df_final.sort_values(by='data').reset_index(drop=True)
        
        # --- MUDANÇA: Criando a nova coluna de tempo formatado ---
        df_final['tempo_bombeamento_hhmm'] = df_final['tempo_total_bombeamento_horas'].apply(converter_horas_para_hhmm)
        
        df_final['vazao_diaria'] = df_final['vazao_total_final'].diff().fillna(0)
        df_final['porcentagem_consumo_vazao'] = round((df_final['vazao_diaria'] / df_final['vazao_outorgada']) * 100, 2).fillna(0)
        
        # Adicionando a nova coluna à ordem final
        ordem_colunas = ['data', 'hora_final', 'vazao_total_final', 'vazao_diaria', 'tempo_total_bombeamento_horas', 'tempo_bombeamento_hhmm', 'vazao_outorgada', 'porcentagem_consumo_vazao']
        df_final = df_final[ordem_colunas]
        num_dias = len(df_final)
        
        consumo_mensal_total = df_final['vazao_diaria'].sum()
        outorga_mensal_total = df_final['vazao_outorgada'].sum()
        tempo_bombeamento_total_decimal = df_final['tempo_total_bombeamento_horas'].sum()
        porcentagem_mensal_total = (round((consumo_mensal_total / outorga_mensal_total) * 100, 2) if outorga_mensal_total > 0 else 0)
        
        # Convertendo o tempo total para o formato HH:MM
        tempo_bombeamento_total_hhmm = converter_horas_para_hhmm(tempo_bombeamento_total_decimal)
        
        df_final['data'] = df_final['data'].dt.strftime('%d/%m/%Y')
        
        df_total_row = pd.DataFrame([{'data': 'TOTAL MENSAL', 'vazao_diaria': consumo_mensal_total, 
                                      'tempo_total_bombeamento_horas': tempo_bombeamento_total_decimal,
                                      'tempo_bombeamento_hhmm': tempo_bombeamento_total_hhmm,
                                      'vazao_outorgada': outorga_mensal_total, 'porcentagem_consumo_vazao': porcentagem_mensal_total}])
        df_final = pd.concat([df_final, df_total_row], ignore_index=True)

        # Adicionando o nome da nova coluna para exibição
        nomes_visuais = {'data': 'Data', 'hora_final': 'Hora Leitura', 'vazao_total_final': 'Leitura do medidor em m³ acumulado', 
                         'vazao_diaria': 'Consumo (m³/dia)', 'tempo_total_bombeamento_horas': 'Tempo Total de Bombeamento (h)',
                         'tempo_bombeamento_hhmm': 'Tempo Total de Bombeamento (h:min)',
                         'vazao_outorgada': 'Vazão Outorgada Diária (m³)', 'porcentagem_consumo_vazao': 'Consumo Diário x Vazão Outorgada (%)'}
        df_final_formatado = df_final.rename(columns=nomes_visuais)

        # --- Criação do Arquivo Excel em Memória ---
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final_formatado.to_excel(writer, sheet_name='Resumo Mensal', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Resumo Mensal']

            header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center', 'fg_color': '#D7E4BC', 'border': 1})
            decimal_format = workbook.add_format({'num_format': '#,#00.00', 'align': 'center', 'valign': 'vcenter'})
            integer_format = workbook.add_format({'num_format': '#,##0', 'align': 'center', 'valign': 'vcenter'})
            text_format = workbook.add_format({'num_format': '@', 'align': 'center', 'valign': 'vcenter'})

            for col_num, value in enumerate(df_final_formatado.columns.values):
                worksheet.write(0, col_num, value, header_format)

            # Ajustando a formatação das colunas para incluir a nova
            worksheet.set_column('A:A', 18) # Data
            worksheet.set_column('B:B', 18) # Hora Final Leitura
            worksheet.set_column('C:C', 22, integer_format) # Vazão Acumulada Final
            worksheet.set_column('D:D', 20, integer_format) # Consumo Diário (m³)
            worksheet.set_column('E:E', 25, integer_format) # Tempo de Bombeamento (h)
            worksheet.set_column('F:F', 15, text_format) # Tempo (HH:MM)
            worksheet.set_column('G:G', 20, integer_format) # Outorga Diária (m³)
            worksheet.set_column('H:H', 25, integer_format) # % Consumido da Outorga

            # Ajustando a referência da Outorga no gráfico para a coluna G
            chart = workbook.add_chart({'type': 'column'})
            chart.add_series({'name': "='Resumo Mensal'!$D$1", 'categories': f"='Resumo Mensal'!$A$2:$A${num_dias + 1}", 'values': f"='Resumo Mensal'!$D$2:$D${num_dias + 1}"})
            chart.add_series({'name': "='Resumo Mensal'!$G$1", 'values': f"='Resumo Mensal'!$G$2:$G${num_dias + 1}"})
            chart.set_title({'name': 'Consumo Diário vs. Outorga Diária'})
            chart.set_x_axis({'name': 'Dia'}); chart.set_y_axis({'name': 'Volume (m³)'})
            worksheet.insert_chart('J2', chart, {'x_scale': 1.5, 'y_scale': 1.5}) # Movido para a coluna J

        return output.getvalue()

    except Exception as e:
        st.error(f"Ocorreu um erro geral durante o processamento: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None

# ============================================================================
# INTERFACE DO USUÁRIO COM STREAMLIT
# ============================================================================
st.set_page_config(page_title="Gerador de Resumo Mensal", layout="centered")
st.title("Resumo de Consumo Mensal (Hidrômetro)")
st.write("Por favor, envie o arquivo .ZIP com os relatórios diários para gerar o resumo em Excel.")
outorga_input = st.number_input(
    label="Defina a Outorga Diária (m³):",
    min_value=0,
    value=9600,
    step=100
)
uploaded_file = st.file_uploader("Escolha o arquivo ZIP", type="zip")
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    with st.spinner("Processando os arquivos... Por favor, aguarde."):
        resultado_excel = processar_zip(bytes_data, outorga_input)
    if resultado_excel:
        st.success("Resumo gerado com sucesso!")
        st.download_button(
            label="Baixar Resumo em Excel",
            data=resultado_excel,
            file_name="resumo_mensal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )