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
from utils import descargar_archivo_contenido
import unittest
import pytest
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
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

# Selector de framework de prueba
test_framework = st.radio("Selecciona el framework para generar los tests:", ("unittest", "pytest"))

def eliminar_caracteres_innecesarios(codigo):
    """
    Elimina caracteres innecesarios del código.

    Args:
        codigo (str): El código del cual se eliminarán los caracteres innecesarios.

    Returns:
        str: El código sin los caracteres innecesarios.
    """
    codigo = codigo.replace("```", "")
    codigo = codigo.replace("python", "")
    lineas = codigo.split('\n')
    lineas = [linea for linea in lineas if not (linea.startswith('from my_module import') or linea.startswith('from mi_modulo import') or linea.startswith('from your_module import') or linea.startswith('from my_code import') or linea.startswith('from mycode import'))]
    codigo_sin_import = '\n'.join(lineas)
    return codigo_sin_import



def obtener_contenido_archivo_desde_github(url):
    """
    Obtiene el contenido de un archivo desde un repositorio de GitHub.

    Args:
        url (str): La URL del archivo en el repositorio de GitHub.

    Returns:
        str: El contenido del archivo.
    """
    raw_url = url.replace("github.com", "raw.githubusercontent.com")
    # Reemplaza '/blob/' por '/' en la URL para obtener el enlace directo al archivo
    raw_url = raw_url.replace("/blob/", "/")
    response = requests.get(raw_url)
    if response.status_code == 200:
        return response.text
    else:
        return None
    
def ejecutar_tests(tests_openai, test_framework):
    # Guardar el código de los tests en un archivo temporal
    with open("test_temp.py", "w") as f:
        f.write(tests_openai)
    
    if test_framework == 'pytest':
        """
        Ejecuta los tests generados y captura los resultados.
    
        Args:
            test_code (str): El código de los tests a ejecutar.
    
        Returns:
            str: Los resultados de la ejecución de los tests.
        """
        # Ejecutar pytest
        result = pytest.main(["test_temp.py"])
        if result == 0:
            st.info("Los tests se han ejecutado correctamente")
        else:
            st.error("Algunos tests fallaron, pero no se puede acceder a los errores con pytest para devolverlos a la api")

    elif test_framework == 'unittest':
        # Importar el módulo de tests temporalmente
        spec = importlib.util.spec_from_file_location("test_temp", "test_temp.py")
        test_temp = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(test_temp)
        
        # Crear un cargador de tests y una suite
        loader = unittest.TestLoader()
        suite = unittest.TestSuite()
        
        # Cargar tests desde el módulo importado
        for name, obj in vars(test_temp).items():
            if isinstance(obj, type) and issubclass(obj, unittest.TestCase):
                suite.addTests(loader.loadTestsFromTestCase(obj))
        
        # Crear un runner para ejecutar los tests y capturar el resultado
        runner = unittest.TextTestRunner(verbosity=2)
        result = runner.run(suite)
        
        # Mostrar el resultado en Streamlit
        if result.wasSuccessful():
            st.info("Los tests se han ejecutado correctamente")
        else:
            st.error("Algunos tests fallaron, vamos a pasarle el código a la API a ver si puede corregirlo")
            for error in result.errors:
                st.error(f"Error: {error[1]}")
            test_corr = test.get_tests_error(tests_openai, result.errors)
            test_corr = eliminar_caracteres_innecesarios(test_corr)
            ejecutar_tests_error(test_corr)
    
    # Eliminar el archivo temporal
    os.remove("test_temp.py")


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
    """
    Función principal que controla la lógica de la aplicación de Streamlit.

    Crea pestañas para ingresar una URL de repositorio o cargar un archivo Python,
    y genera tests unitarios basados en el contenido proporcionado.
    """
    
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
                    tests_openai = test.get_tests(contenido, test_framework)
                    tests_openai = eliminar_caracteres_innecesarios(tests_openai)
                    if contenido:
                        # Mostrar el contenido en un componente de Streamlit
                        st.code(tests_openai, language="python")
                        contenido_y_tests = ejecutar_contenido(contenido, tests_openai)
                        ejecutar_tests(contenido_y_tests, test_framework)
                        
                        # Botón de descarga usando la función importada
                        descargar_archivo_contenido('test_unitario_generado.py', tests_openai)
                    
                        #Esto todavía falla
                        #ejecucion_tests =  exec(tests_openai) #Esto todavía falla
                        #st.warning(ejecucion_tests)
                    else:
                        st.error("No se pudo obtener el contenido del archivo. Verifica los detalles del repositorio y la ruta del archivo.")
                else:
                    st.warning("Por favor, ingresa todos los detalles del repositorio y la ruta del archivo.")
                                               # Botón de descarg
                
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
                    tests_openai = test.get_tests(code, test_framework)
                    test_unitario = eliminar_caracteres_innecesarios(tests_openai)
                    # Mostrar el contenido en un componente de Streamlit
                    st.write('Test Unitario generado:')
                    st.code(test_unitario, language="python")
                    contenido_y_tests = ejecutar_contenido(code, test_unitario)
                    ejecutar_tests(contenido_y_tests, test_framework)                
                     
                    # Botón de descarga usando la función importada
                    descargar_archivo_contenido('test_unitario_generado.py', test_unitario)

                    
                    )

if __name__ == "__main__":
    main()
