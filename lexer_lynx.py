import ply.lex as lex
from collections import defaultdict
import sys

reserved = {
    'y': 'Y',
    'salir': 'SALIR',
    'hacer': 'HACER',
    'sino': 'SINO',
    'sinosi': 'SINOSI',
    'falso': 'FALSO',
    'para': 'PARA',
    'fun': 'FUN',
    'si': 'SI',
    'en': 'EN',
    'val': 'VAL',
    'nulo': 'NULO',
    'no': 'NO',
    'o': 'O',
    'repetir': 'REPETIR',
    'retornar': 'RETORNAR',
    'entonces': 'ENTONCES',
    'verdadero': 'VERDADERO',
    'hasta': 'HASTA',
    'mientras': 'MIENTRAS',
    'intentar': 'INTENTAR',
    'capturar': 'CAPTURAR',
    'segun': 'SEGUN',
    'caso': 'CASO',
    'finalmente': 'FINALMENTE',
    'parar': 'PARAR',
    'predeterminado': 'PREDETERMINADO',
    'imprimir': 'IMPRIMIR'
}

tokens = [
    'ID', 'NUMERO', 'FLOTANTE', 'CADENA',
    'MAS', 'MENOS', 'POR', 'DIV', 'MOD',
    'IGUAL', 'DIFERENTE', 'MENOR', 'MAYOR', 'MENOR_IGUAL', 'MAYOR_IGUAL',
    'PAREN_ABRIR', 'PAREN_CERRAR', 'LLAVE_ABRIR', 'LLAVE_CERRAR', 
    'CORCHETE_ABRIR', 'CORCHETE_CERRAR',
    'COMENTARIO_LINEA', 'COMENTARIO_BLOQUE',
    'SEPARADOR', 'ASIGNACION', 'CASE_LIMITADOR', 'PUNTO_COMA'
] + list(reserved.values())

# Tokens simples
t_MAS = r'\+'
t_MENOS = r'-'
t_POR = r'\*'
t_DIV = r'/'
t_MOD = r'%'
t_IGUAL = r'=='
t_DIFERENTE = r'!='
t_MENOR = r'<'
t_MAYOR = r'>'
t_MENOR_IGUAL = r'<='
t_MAYOR_IGUAL = r'>='
t_PAREN_ABRIR = r'\('
t_PAREN_CERRAR = r'\)'
t_LLAVE_ABRIR = r'\{'
t_LLAVE_CERRAR = r'\}'
t_CORCHETE_ABRIR = r'\['
t_CORCHETE_CERRAR = r'\]'
t_SEPARADOR = r'[,]'
t_PUNTO_COMA = r';'
t_ASIGNACION = r'='
t_CASE_LIMITADOR = r':'

# Ignorar espacios y tabs
t_ignore = ' \t'

def t_FLOTANTE(t):
    r'\d+\.\d+'
    t.value = float(t.value)
    return t

def t_NUMERO(t):
    r'\d+'
    t.value = int(t.value)
    return t

def t_CADENA(t):
    r'"[^"]*"|\'[^\']*\''
    t.value = t.value[1:-1]
    return t

def t_COMENTARIO_BLOQUE(t):
    r'/\*[\s\S]*?\*/'
    t.lexer.lineno += t.value.count('\n')
    pass

def t_COMENTARIO_LINEA(t):
    r'\/\/.*'
    pass

def t_ID(t):
    r'[a-zA-Z_][a-zA-Z0-9_]*'
    t.type = reserved.get(t.value, 'ID')
    return t

def t_newline(t):
    r'\n+'
    t.lexer.lineno += len(t.value)

def t_error(t):
    linea = t.lineno
    columna = obtener_columna(t.lexer.lexdata, t)
    print(f"Error léxico: caracter no reconocido '{t.value[0]}' en la línea {linea}, columna {columna}")
    t.lexer.skip(1)

def obtener_columna(input_text, token):
    last_newline = input_text.rfind('\n', 0, token.lexpos)
    if last_newline < 0:
        last_newline = -1
    return len(input_text[last_newline+1:token.lexpos])

def crear_lexer():
    return lex.lex()

def analizar_lexico(entrada):
    lexer = crear_lexer()
    lexer.input(entrada)
    
    tokens_resultado = []
    errores = []
    
    for token in lexer:
        columna = obtener_columna(entrada, token)
        tokens_resultado.append({
            'lexema': str(token.value),
            'tipo': token.type,
            'linea': token.lineno,
            'columna': columna
        })
    
    return tokens_resultado, errores

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python analizador.py <archivo.lynx>")
        sys.exit(1)
    
    archivo = sys.argv[1]
    if not archivo.endswith('.lynx'):
        print("Error: el archivo debe tener extensión .lynx")
        sys.exit(1)
    
    try:
        with open(archivo, 'r', encoding='utf-8') as file:
            contenido = file.read()
            tokens, errores = analizar_lexico(contenido)
            
            print(f"{'Lexema':<20} {'Tipo':<20} {'Línea':<10} {'Columna':<10}")
            print("="*60)
            
            for token in tokens:
                print(f"{token['lexema']:<20} {token['tipo']:<20} {token['linea']:<10} {token['columna']:<10}")
                
    except FileNotFoundError:
        print(f"El archivo {archivo} no fue encontrado.")
        sys.exit(1)
