import streamlit as st
import openai
import requests
from dotenv import load_dotenv
import os
import test
import tempfile
import subprocess
import re
import sys

import unittest
import pandas as pd
from sklearn.preprocessing import MinMaxScaler  # Asegúrate de que está importado
import importlib.util

load_dotenv()

# Configurar la API de OpenAI
api_key = os.environ.get('OPENAI_API_KEY')

openai.api_key = api_key

# Crear una fila para los logos en la esquina superior izquierda
# col1, col2, col3 = st.columns([1, 6, 1])
# with col1:
#     st.image('../images/soprasteria_logo.jpg', width=100)
# with col3:
#     st.image('../images/unir_universidad_internet_logo.jpg', width=100)

# Título de la aplicación
st.title('Generador de tests unitarios mediante IA Generativa')



# Información de autores y tutor
st.header('Autores:')
st.write('''
- Rafael Alvear  
- Samuel Burgueño
''')
st.write('Tutor: Pablo Guijarro')


def eliminar_caracteres_innecesarios(codigo):
    codigo = codigo.replace("```", "")
    codigo = codigo.replace("python", "")
    lineas = codigo.split('\n')
    lineas = [linea for linea in lineas if not (linea.startswith('from my_module import') or linea.startswith('from mi_modulo import') or linea.startswith('from your_module import') or linea.startswith('from my_code import') or linea.startswith('from mycode import'))]
    codigo_sin_import = '\n'.join(lineas)
    return codigo_sin_import



def obtener_contenido_archivo_desde_github(url):
    raw_url = url.replace("github.com", "raw.githubusercontent.com")
    # Reemplaza '/blob/' por '/' en la URL para obtener el enlace directo al archivo
    raw_url = raw_url.replace("/blob/", "/")
    response = requests.get(raw_url)
    if response.status_code == 200:
        return response.text
    else:
        return None
    
def ejecutar_tests(tests_openai):
    # Guardar el código de los tests en un archivo temporal
    with open("temp_tests.py", "w") as f:
        f.write(tests_openai)
    
    # Importar el módulo de tests temporalmente
    spec = importlib.util.spec_from_file_location("temp_tests", "temp_tests.py")
    temp_tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(temp_tests)
    
    # Crear un cargador de tests y una suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Cargar tests desde el módulo importado
    for name, obj in vars(temp_tests).items():
        if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
            suite.addTests(loader.loadTestsFromTestCase(obj))
    
    # Crear un runner para ejecutar los tests y capturar el resultado
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar el resultado en Streamlit
    if result.wasSuccessful():
        st.info("Los tests se han ejecutado correctamente")
    else:
        st.error("Algunos tests fallaron, vamos a pasarle elcódigo a la api a ver si puede corregirlo")
        for error in result.errors:
            st.error(f"Error: {error[1]}")
            test_corr = test.get_tests_error(tests_openai, result.errors)
            test_corr = eliminar_caracteres_innecesarios(test_corr)
            ejecutar_tests_error(test_corr)
    # Eliminar el archivo temporal
    os.remove("temp_tests.py")

def ejecutar_tests_error(tests_openai):
    # Guardar el código de los tests en un archivo temporal
    with open("temp_tests_e.py", "w") as f:
        f.write(tests_openai)
    
    # Importar el módulo de tests temporalmente
    spec = importlib.util.spec_from_file_location("temp_tests_e", "temp_tests_e.py")
    temp_tests = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(temp_tests)
    
    # Crear un cargador de tests y una suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Cargar tests desde el módulo importado
    for name, obj in vars(temp_tests).items():
        if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
            suite.addTests(loader.loadTestsFromTestCase(obj))
    
    # Crear un runner para ejecutar los tests y capturar el resultado
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Mostrar el resultado en Streamlit
    if result.wasSuccessful():
        st.info("Los tests se han ejecutado correctamente")
    else:
        st.error(f"Error al ejecutar los tests definitivos")
        for error in result.errors:
            st.error(f"Error: {error[1]}")
            
    # Eliminar el archivo temporal
    os.remove("temp_tests_e.py")


# Se genera el código del test, se guarda en un archivo temporal y luego se ejecuta ese archivo dentro de la aplicación Streamlit, mostrando los resultados en la interfaz
# """def ejecutar_test(codigo_test):
#     # Guardar el código del test en un archivo temporal
#     with tempfile.NamedTemporaryFile(delete=False, suffix=".py") as temp_file:
#         temp_file.write(codigo_test.encode('utf-8'))
#         temp_file.flush()
        
#         # Ejecutar el archivo de test y capturar la salida
#         resultado = subprocess.run(['python', temp_file.name], capture_output=True, text=True)
#         return resultado.stdout, resultado.stderr


# def dividir_tests_en_funciones(codigo_test):
#     funciones = codigo_test.split("def ")
#     funciones = ["def " + f for f in funciones if f.strip()]
#     return funciones
# """

def ejecutar_contenido(contenido, tests_openai):
    try:
        exec(contenido)
    except ModuleNotFoundError as e: #si hay módulos del script que no tenemos instalados, se instalan
        modulo = re.search(r"No module named '([^']+)'", e.msg)
        modulo = modulo.group(1)
        subprocess.check_call([sys.executable, "-m", "pip", "install", modulo])
        try:
            exec(contenido)
        except Exception as e:
            st.error(f"Error al ejecutar el código del que dependen los tests: {e}")
    except Exception as e:
        st.error(f"Ha fallado el código con el siguiente error, pero se va a consultar de nuevo con openai: {e}")
        try:
            contenido = test.get_contenido_error(contenido, e.args[0])
            contenido = eliminar_caracteres_innecesarios(contenido)
            exec(contenido)
        except:
            st.error(f"Error al ejecutar el código que ha devuelto gpt: {e}")
    contenido_y_tests = contenido + "\n" + tests_openai
    return contenido_y_tests

def main():
    # Crear pestañas
    tab1, tab2 = st.tabs(["Ingresar URL del repositorio", "Subir archivo Python"])

    with tab1:
        st.header("Generar tests unitarios desde una URL de repositorio en GitHub")
        
        # Inputs para que el usuario ingrese los detalles del repositorio y el archivo
        path = st.text_input("Ingresa la URL del repositorio:")
        
        # Botón para obtener y mostrar el contenido del archivo
        if st.button("Generar tests unitarios para el repositorio de GitHub"):
            with st.spinner('Generando tests unitarios...'):
                if path:
                    contenido = obtener_contenido_archivo_desde_github(path)
                    tests_openai = test.get_tests(contenido)
                    tests_openai = eliminar_caracteres_innecesarios(tests_openai)
                    if contenido:
                        # Mostrar el contenido en un componente de Streamlit
                        st.code(tests_openai, language="python")
                        contenido_y_tests = ejecutar_contenido(contenido, tests_openai)
                        ejecutar_tests(contenido_y_tests)

                         #Esto todavía falla
                        #ejecucion_tests =  exec(tests_openai) #Esto todavía falla
                        #st.warning(ejecucion_tests)
                    else:
                        st.error("No se pudo obtener el contenido del archivo. Verifica los detalles del repositorio y la ruta del archivo.")
                else:
                    st.warning("Por favor, ingresa todos los detalles del repositorio y la ruta del archivo.")
                                               # Botón de descarg
                st.download_button(
                    label="Descargar test generado como archivo .py",
                    data=tests_openai,
                    file_name='test_unitario_generado.py',
                    mime='text/plain'
                )
    with tab2:
        st.header("Generar tests unitarios desde un archivo Python")
        
        # Caja de carga para el archivo .py
        uploaded_file = st.file_uploader("O adjunta tu archivo de Python aquí:")
        
        # Botón para generar el test unitario
        if uploaded_file is not None:
            code = uploaded_file.getvalue().decode("utf-8")
            st.write('Comprueba que el fichero subido es correcto:')
            st.code(code, language="python")
            if st.button('Generar tests unitarios'):
                with st.spinner('Generando tests unitarios...'):
                    tests_openai = test.get_tests(code)
                    test_unitario = eliminar_caracteres_innecesarios(tests_openai)
                    # Mostrar el contenido en un componente de Streamlit
                    st.write('Test Unitario generado:')
                    st.code(test_unitario, language="python")
                    
                
                    
                    # Botón de descarga
                    st.download_button(
                        label="Descargar test generado como archivo .py",
                        data=test_unitario,
                        file_name='test_unitario_generado.py',
                        mime='text/plain'
                    )

                # Botón para ejecutar el test
                """ if st.button('Ejecutar test unitario'):
                    with st.spinner('Ejecutando test unitario...'):
                        salida, error = ejecutar_test(test_unitario)
                        st.write('Resultado de la ejecución del test:')
                        if salida:
                            st.text_area('Salida', salida, height=200)
                        if error:
                            st.text_area('Error', error, height=200, text_color="red")
                """

if __name__ == "__main__":
    main()