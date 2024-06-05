import openai
from dotenv import load_dotenv
import os

load_dotenv()

def get_tests(code, test_framework):
  # Access the environment variables from the .env file
  api_key = os.environ.get('OPENAI_API_KEY')

  openai.api_key = api_key
  client = openai.OpenAI()

  if test_framework == "pytest":
    prompt = "Genera los tests unitarios utilizando pytest para las funciones definidas en el siguiente código: " + code
  elif test_framework == "unittest":
    prompt = "Genera los tests unitarios utilizando unittest para las funciones definidas en el siguiente código: " + code
  else:
    raise ValueError("El framework de test especificado no es válido. Debe ser 'pytest' o 'unittest'.")

  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "Solamente puedes devolver código en python, no devuelvas nada que no sea código python"},
      {"role": "user", "content": prompt}
    ]
  )

  print(completion.choices[0].message.content)
  codigo = completion.choices[0].message.content
  return codigo

def get_contenido_error(code, error):
  # Access the environment variables from the .env file
  api_key = os.environ.get('OPENAI_API_KEY')

  openai.api_key = api_key
  client = openai.OpenAI()


  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "Solamente puedes devolver código en python"},
      {"role": "user", "content": f"Ejecutando el siguiente código: ```{code}```. He obtenido el siguiente error: {error}. Devuelve solo el código corregido sin explicaciones."}
    ]
  )

  print(completion.choices[0].message.content)
  codigo = completion.choices[0].message.content
  return codigo

def get_tests_error(code, error):
  # Access the environment variables from the .env file
  api_key = os.environ.get('OPENAI_API_KEY')

  openai.api_key = api_key
  client = openai.OpenAI()


  completion = client.chat.completions.create(
    model="gpt-3.5-turbo",
    messages=[
      {"role": "system", "content": "Solamente puedes devolver código en python"},
      {"role": "user", "content": f"Ejecutando el siguiente código: ```{code}```. He obtenido el siguiente error: {error}. Devuelve solo el código corregido sin explicaciones."}
    ]
  )

  print(completion.choices[0].message.content)
  codigo = completion.choices[0].message.content
  return codigo