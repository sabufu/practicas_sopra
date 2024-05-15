import streamlit as st
import openai
from dotenv import load_dotenv
import os

load_dotenv()

# Configurar la API de OpenAI
api_key = os.environ.get('OPENAI_API_KEY')

openai.api_key = api_key

# Crear una fila para los logos en la esquina superior izquierda
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    st.image('../images/soprasteria_logo.jpg', width=100)
with col3:
    st.image('../images/unir_universidad_internet_logo.jpg', width=100)

# Título de la aplicación
st.title('Generador de tests unitarios mediante IA Generativa')



# Información de autores y tutor
st.header('Autores:')
st.write('''
- Rafael Alvear  
- Samuel Burgueño
''')
st.write('Tutor: Pablo Guijarro')



# Caja de carga para el archivo .py
uploaded_file = st.file_uploader("Adjunta tu archivo .py aquí")

# Botón para generar el test unitario
if uploaded_file is not None:
    code = uploaded_file.getvalue().decode("utf-8")
    st.text_area("Código Python cargado:", value=code)
    if st.button('Generar Test Unitario'):
        completion = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            max_tokens=100,
            messages=[
            {"role": "system", "content": "Solamente puedes devolver código en python"},
            {"role": "user", "content": f"Genera los tests unitarios para las funciones en el archivo cargado:\n\n{code}"}
            ]
        )
        test_unitario = completion.choices[0].message.content
        st.write('Test Unitario generado:')
        st.write(test_unitario)
