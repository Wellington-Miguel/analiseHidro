import streamlit as st
import pandas as pd
from zipfile import ZipFile
import io


def processar_zip(arquivo_zip_bytes, outorga_diaria_definida):
    
    # Função auxiliar para converter horas decimais para o formato de texto HH:MM
    def converter_horas_para_hhmm(horas_decimais):
        if pd.isna(horas_decimais):
            return ""
        horas = int(horas_decimais)
        minutos = int(round((horas_decimais - horas) * 60))
        return f"{horas:02d}:{minutos:02d}"

    try:
        #Limpar cada ficheiro individualmente e detectar formato ---
        lista_de_dfs_limpos = []
        with ZipFile(io.BytesIO(arquivo_zip_bytes), 'r') as zip_ref:
            arquivos_csv = sorted([f for f in zip_ref.namelist() if f.upper().endswith('.CSV')])
            
            if not arquivos_csv:
                st.error("Nenhum ficheiro .csv ou .CSV foi encontrado dentro do ficheiro ZIP.")
                return None

            for arquivo in arquivos_csv:
                with zip_ref.open(arquivo) as f:
                    # Detecção automática do separador e da posição da vazão
                    primeira_linha = f.readline().decode('iso-8859-1')
                    f.seek(0)

                    if ';' in primeira_linha:
                        separador = ';'
                        posicao_vazao = 4
                    else:
                        separador = ','
                        posicao_vazao = 5
                    
                    df_diario = pd.read_csv(f, encoding='ISO-8859-1', header=None, sep=separador)
                    
                    if df_diario.empty or df_diario.shape[1] <= posicao_vazao:
                        continue

                    #Limpa os dados de cada ficheiro
                    df_limpo = df_diario.iloc[:, [1, 2, posicao_vazao]].copy()
                    df_limpo.columns = ['data_str', 'hora_str', 'vazao_total']
                    
                    df_limpo['vazao_total'] = pd.to_numeric(
                        df_limpo['vazao_total'].astype(str).str.replace(',', '.'), 
                        errors='coerce'
                    )
                    df_limpo.dropna(subset=['vazao_total'], inplace=True)
                    
                    if not df_limpo.empty:
                        lista_de_dfs_limpos.append(df_limpo)

        if not lista_de_dfs_limpos:
            st.error("Nenhum dado válido pôde ser extraído dos ficheiros CSV.")
            return None

        #Ordenar tabela inicial
        df_master = pd.concat(lista_de_dfs_limpos, ignore_index=True)
        
        df_master['datetime'] = pd.to_datetime(df_master['data_str'] + ' ' + df_master['hora_str'], format='%Y/%m/%d %H:%M:%S', errors='coerce')
        df_master.dropna(subset=['datetime'], inplace=True)
        df_master = df_master.sort_values(by='datetime').reset_index(drop=True)

        #Calcular a variação na sequência contínua
        df_master['dif_vazao'] = df_master['vazao_total'].diff()
        df_master['bombeamento'] = (df_master['dif_vazao'] >= 2)
        df_master['data'] = df_master['datetime'].dt.date

        #Agrupar por dia 
        resumo_bombeamentos = df_master.groupby('data')['bombeamento'].sum().reset_index()
        resumo_bombeamentos.rename(columns={'bombeamento': 'num_bombeamentos'}, inplace=True)

        resumo_leituras = df_master.groupby('data').agg(
            hora_final=('hora_str', 'last'),
            vazao_total_final=('vazao_total', 'last')
        ).reset_index()
        
        df_final = pd.merge(resumo_leituras, resumo_bombeamentos, on='data')
        
        #Calcular as colunas finais do relatório
        df_final['tempo_total_bombeamento_horas'] = (df_final['num_bombeamentos'] * 15) / 60
        df_final['tempo_bombeamento_hhmm'] = df_final['tempo_total_bombeamento_horas'].apply(converter_horas_para_hhmm)
        df_final['vazao_outorgada'] = outorga_diaria_definida
        df_final['vazao_diaria'] = df_final['vazao_total_final'].diff().fillna(0)
        df_final['porcentagem_consumo_vazao'] = round((df_final['vazao_diaria'] / df_final['vazao_outorgada']) * 100, 2).fillna(0)

        ordem_colunas = ['data', 'hora_final', 'vazao_total_final', 'vazao_diaria', 'tempo_total_bombeamento_horas', 'tempo_bombeamento_hhmm', 'vazao_outorgada', 'porcentagem_consumo_vazao']
        df_final = df_final[ordem_colunas]
        num_dias = len(df_final)
        
        consumo_mensal_total = df_final['vazao_diaria'].sum()
        outorga_mensal_total = df_final['vazao_outorgada'].sum()
        tempo_bombeamento_total_decimal = df_final['tempo_total_bombeamento_horas'].sum()
        porcentagem_mensal_total = (round((consumo_mensal_total / outorga_mensal_total) * 100, 2) if outorga_mensal_total > 0 else 0)
        tempo_bombeamento_total_hhmm = converter_horas_para_hhmm(tempo_bombeamento_total_decimal)
        
        df_final['data'] = pd.to_datetime(df_final['data']).dt.strftime('%d/%m/%Y')
        
        df_total_row = pd.DataFrame([{'data': 'TOTAL MENSAL', 'vazao_diaria': consumo_mensal_total, 
                                      'tempo_total_bombeamento_horas': tempo_bombeamento_total_decimal,
                                      'tempo_bombeamento_hhmm': tempo_bombeamento_total_hhmm,
                                      'vazao_outorgada': outorga_mensal_total, 'porcentagem_consumo_vazao': porcentagem_mensal_total}])
        df_final = pd.concat([df_final, df_total_row], ignore_index=True)

        nomes_visuais = {'data': 'Data', 'hora_final': 'Hora Leitura', 'vazao_total_final': 'Leitura do medidor em m³ acumulado', 
                         'vazao_diaria': 'Consumo (m³/dia)', 'tempo_total_bombeamento_horas': 'Tempo Total de Bombeamento (h)',
                         'tempo_bombeamento_hhmm': 'Tempo Total de Bombeamento (h:min)',
                         'vazao_outorgada': 'Vazão Outorgada Diária (m³)', 'porcentagem_consumo_vazao': 'Consumo Diário x Vazão Outorgada (%)'}
        df_final_formatado = df_final.rename(columns=nomes_visuais)

        #Criação do Arquivo Excel 
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            df_final_formatado.to_excel(writer, sheet_name='Resumo Mensal', index=False)
            
            workbook = writer.book
            worksheet = writer.sheets['Resumo Mensal']

            header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'vcenter', 'align': 'center', 'fg_color': '#dce6f1', 'border': 1})
            decimal_format = workbook.add_format({'num_format': '#,#00.00', 'align': 'center', 'valign': 'vcenter'})
            integer_format = workbook.add_format({'num_format': '#,##0', 'align': 'center', 'valign': 'vcenter'})
            text_format = workbook.add_format({'num_format': '@', 'align': 'center', 'valign': 'vcenter'})

            for col_num, value in enumerate(df_final_formatado.columns.values):
                worksheet.write(0, col_num, value, header_format)

            worksheet.set_column('A:A', 18, text_format)
            worksheet.set_column('B:B', 18, text_format)
            worksheet.set_column('C:C', 35, integer_format)
            worksheet.set_column('D:D', 20, integer_format)
            worksheet.set_column('E:E', 30, decimal_format)
            worksheet.set_column('F:F', 35, text_format)
            worksheet.set_column('G:G', 30, integer_format)
            worksheet.set_column('H:H', 40, decimal_format)

            chart = workbook.add_chart({'type': 'column'})
            chart.add_series({'name': "='Resumo Mensal'!$D$1", 'categories': f"='Resumo Mensal'!$A$2:$A${num_dias + 1}", 'values': f"='Resumo Mensal'!$D$2:$D${num_dias + 1}"})
            chart.add_series({'name': "='Resumo Mensal'!$G$1", 'values': f"='Resumo Mensal'!$G$2:$G${num_dias + 1}"})
            chart.set_title({'name': 'Consumo Diário X Vazão Outorgada'})
            chart.set_x_axis({'name': 'Dia'}); chart.set_y_axis({'name': 'Volume (m³)'})
            worksheet.insert_chart('J2', chart, {'x_scale': 1.5, 'y_scale': 1.5})

        return output.getvalue()

    except Exception as e:
        st.error(f"Ocorreu um erro geral durante o processamento: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None


# INTERFACE DO USUÁRIO 
st.set_page_config(page_title="Gerador de Resumo Mensal", layout="centered")
st.title("Resumo de Consumo Mensal (Hidrômetro)")
st.write("Por favor, envie o ficheiro .ZIP com os relatórios diários para gerar o resumo em Excel.")
outorga_input = st.number_input(
    label="Defina a Outorga Diária (m³):",
    min_value=0,
    value=9600,
    step=100
)
uploaded_file = st.file_uploader("Escolha o ficheiro ZIP", type="zip")
if uploaded_file is not None:
    bytes_data = uploaded_file.getvalue()
    with st.spinner("A processar os ficheiros... Por favor, aguarde."):
        resultado_excel = processar_zip(bytes_data, outorga_input)
    if resultado_excel:
        st.success("Resumo gerado com sucesso!")
        st.download_button(
            label="Baixar Resumo em Excel",
            data=resultado_excel,
            file_name="resumo_mensal.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
