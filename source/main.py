import streamlit as st
import requests
import test

def eliminar_caracteres_innecesarios(codigo):
    codigo = codigo.replace("```", "")
    codigo = codigo.replace("python", "")
    return codigo

def obtener_contenido_archivo_desde_github(url):
    raw_url = url.replace("github.com", "raw.githubusercontent.com")
    # Reemplaza '/blob/' por '/' en la URL para obtener el enlace directo al archivo
    raw_url = raw_url.replace("/blob/", "/")
    response = requests.get(raw_url)
    if response.status_code == 200:
        return response.text
    else:
        return None

def main():
    st.title("Visualizador de Tests de GitHub")
    
    # Inputs para que el usuario ingrese los detalles del repositorio y el archivo
    path = st.text_input("Ingresa la url del repositorio :")

    
    # Botón para obtener y mostrar el contenido del archivo
    if st.button("Ver Tests del siguiente repositorio en github"):
        if path:
            contenido = obtener_contenido_archivo_desde_github(path)
            tests_openai = test.get_tests(contenido)
            tests_openai = eliminar_caracteres_innecesarios(tests_openai)
            if contenido:
                # Mostrar el contenido en un componente de Streamlit
                st.code(tests_openai, language="python")
                #ejecucion_tests =  exec(tests_openai) #Esto todavía falla
                #st.warning(ejecucion_tests)
            else:
                st.error("No se pudo obtener el contenido del archivo. Verifica los detalles del repositorio y la ruta del archivo.")
        else:
            st.warning("Por favor, ingresa todos los detalles del repositorio y la ruta del archivo.")

if __name__ == "__main__":
    main()
