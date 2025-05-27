import ply.yacc as yacc
from lexer_lynx import tokens, crear_lexer

# Precedencia de operadores
precedence = (
    ('left', 'O'),
    ('left', 'Y'),
    ('right', 'NO'),
    ('left', 'IGUAL', 'DIFERENTE'),
    ('left', 'MENOR', 'MAYOR', 'MENOR_IGUAL', 'MAYOR_IGUAL'),
    ('left', 'MAS', 'MENOS'),
    ('left', 'POR', 'DIV', 'MOD'),
    ('right', 'UMINUS', 'UPLUS'),
)

# AST Node classes
class ASTNode:
    pass

class Programa(ASTNode):
    def __init__(self, instrucciones):
        self.instrucciones = instrucciones

class DeclaracionVariable(ASTNode):
    def __init__(self, nombre, valor=None):
        self.nombre = nombre
        self.valor = valor

class AsignacionVariable(ASTNode):
    def __init__(self, nombre, valor):
        self.nombre = nombre
        self.valor = valor

class DeclaracionArreglo(ASTNode):
    def __init__(self, nombre, elementos):
        self.nombre = nombre
        self.elementos = elementos

class DeclaracionTabla(ASTNode):
    def __init__(self, nombre, pares):
        self.nombre = nombre
        self.pares = pares

class EstructuraSi(ASTNode):
    def __init__(self, condicion, bloque, sinosis=None):
        self.condicion = condicion
        self.bloque = bloque
        self.sinosis = sinosis

class EstructuraMientras(ASTNode):
    def __init__(self, condicion, bloque):
        self.condicion = condicion
        self.bloque = bloque

class EstructuraPara(ASTNode):
    def __init__(self, init, condicion, incremento, bloque):
        self.init = init
        self.condicion = condicion
        self.incremento = incremento
        self.bloque = bloque

class EstructuraRepetir(ASTNode):
    def __init__(self, bloque, condicion):
        self.bloque = bloque
        self.condicion = condicion

class EstructuraSegun(ASTNode):
    def __init__(self, expresion, casos, predeterminado=None):
        self.expresion = expresion
        self.casos = casos
        self.predeterminado = predeterminado

class Caso(ASTNode):
    def __init__(self, valor, bloque):
        self.valor = valor
        self.bloque = bloque

class DeclaracionFuncion(ASTNode):
    def __init__(self, nombre, parametros, bloque, retorno=None):
        self.nombre = nombre
        self.parametros = parametros
        self.bloque = bloque
        self.retorno = retorno

class Imprimir(ASTNode):
    def __init__(self, elementos):
        self.elementos = elementos

class ExpresionBinaria(ASTNode):
    def __init__(self, izq, op, der):
        self.izq = izq
        self.op = op
        self.der = der

class ExpresionUnaria(ASTNode):
    def __init__(self, op, expr):
        self.op = op
        self.expr = expr

class AccesoArreglo(ASTNode):
    def __init__(self, nombre, indice):
        self.nombre = nombre
        self.indice = indice

class AccesoTabla(ASTNode):
    def __init__(self, nombre, clave):
        self.nombre = nombre
        self.clave = clave

# Reglas de gramática
def p_bloque_codigo(p):
    '''bloque_codigo : instruccion_list
                    | empty'''
    if p[1] is None:
        p[0] = []
    else:
        p[0] = p[1]

def p_instruccion_list(p):
    '''instruccion_list : instruccion_list instruccion
                       | instruccion'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_instruccion(p):
    '''instruccion : declaraciones
                  | estructurasbase
                  | accesos
                  | expresion
                  | imprimir'''
    p[0] = p[1]

def p_declaraciones(p):
    '''declaraciones : declaracion_variable
                    | asignacion_variable
                    | declaracion_arreglo
                    | declaracion_tabla
                    | declaracion_funcion'''
    p[0] = p[1]

def p_estructurasbase(p):
    '''estructurasbase : estructura_si
                      | estructura_mientras
                      | estructura_para
                      | estructura_repetir
                      | estructura_para_cada
                      | estructura_segun
                      | estructura_intentar'''
    p[0] = p[1]

def p_accesos(p):
    '''accesos : acceso_arreglo
              | acceso_tabla'''
    p[0] = p[1]

# Declaraciones
def p_declaracion_simple(p):
    '''declaracion_simple : VAL ID'''
    p[0] = DeclaracionVariable(p[2])

def p_asignacion_variable(p):
    '''asignacion_variable : ID ASIGNACION valor'''
    p[0] = AsignacionVariable(p[1], p[3])

def p_declaracion_variable(p):
    '''declaracion_variable : VAL ID ASIGNACION valor
                           | declaracion_simple'''
    if len(p) == 5:
        p[0] = DeclaracionVariable(p[2], p[4])
    else:
        p[0] = p[1]

# Valores
def p_valor(p):
    '''valor : numero
            | CADENA
            | ID
            | expresion_concatenacion'''
    p[0] = p[1]

def p_numero(p):
    '''numero : NUMERO
             | FLOTANTE
             | MENOS NUMERO %prec UMINUS
             | MENOS FLOTANTE %prec UMINUS'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = -p[2]

# Expresiones
def p_expresion(p):
    '''expresion : expresion_logica'''
    p[0] = p[1]

def p_expresion_logica(p):
    '''expresion_logica : expresion_relacional
                       | expresion_logica Y expresion_relacional
                       | expresion_logica O expresion_relacional
                       | NO expresion_relacional'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = ExpresionUnaria(p[1], p[2])
    else:
        p[0] = ExpresionBinaria(p[1], p[2], p[3])

def p_expresion_relacional(p):
    '''expresion_relacional : termino_relacional
                           | termino_relacional IGUAL termino_relacional
                           | termino_relacional DIFERENTE termino_relacional
                           | termino_relacional MAYOR termino_relacional
                           | termino_relacional MENOR termino_relacional
                           | termino_relacional MAYOR_IGUAL termino_relacional
                           | termino_relacional MENOR_IGUAL termino_relacional'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ExpresionBinaria(p[1], p[2], p[3])

def p_termino_relacional(p):
    '''termino_relacional : expresion_simple
                         | PAREN_ABRIR expresion_aritmetica PAREN_CERRAR'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

def p_expresion_simple(p):
    '''expresion_simple : numero
                       | CADENA
                       | ID
                       | acceso_arreglo
                       | acceso_tabla
                       | expresion_concatenacion'''
    p[0] = p[1]

def p_expresion_aritmetica(p):
    '''expresion_aritmetica : termino
                           | expresion_aritmetica MAS termino
                           | expresion_aritmetica MENOS termino'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ExpresionBinaria(p[1], p[2], p[3])

def p_termino(p):
    '''termino : factor
              | termino POR factor
              | termino DIV factor
              | termino MOD factor'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ExpresionBinaria(p[1], p[2], p[3])

def p_factor(p):
    '''factor : expresion_simple
             | PAREN_ABRIR expresion PAREN_CERRAR
             | MENOS factor %prec UMINUS
             | MAS factor %prec UPLUS'''
    if len(p) == 2:
        p[0] = p[1]
    elif len(p) == 3:
        p[0] = ExpresionUnaria(p[1], p[2])
    else:
        p[0] = p[2]

# Concatenación
def p_expresion_concatenacion(p):
    '''expresion_concatenacion : elemento_concatenable
                              | expresion_concatenacion MAS elemento_concatenable'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = ExpresionBinaria(p[1], p[2], p[3])

def p_elemento_concatenable(p):
    '''elemento_concatenable : CADENA
                            | numero
                            | ID
                            | acceso_arreglo
                            | acceso_tabla
                            | PAREN_ABRIR expresion_concatenacion PAREN_CERRAR'''
    if len(p) == 2:
        p[0] = p[1]
    else:
        p[0] = p[2]

# Imprimir
def p_imprimir(p):
    '''imprimir : IMPRIMIR PAREN_ABRIR elemento_imprimir_list PAREN_CERRAR'''
    p[0] = Imprimir(p[3])

def p_elemento_imprimir_list(p):
    '''elemento_imprimir_list : elemento_imprimir_list SEPARADOR elemento_imprimir
                             | elemento_imprimir'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_elemento_imprimir(p):
    '''elemento_imprimir : CADENA
                        | numero
                        | ID
                        | acceso_arreglo
                        | acceso_tabla
                        | expresion_concatenacion'''
    p[0] = p[1]

# Arreglos
def p_declaracion_arreglo(p):
    '''declaracion_arreglo : VAL ID ASIGNACION CORCHETE_ABRIR elemento_arreglo_list CORCHETE_CERRAR'''
    p[0] = DeclaracionArreglo(p[2], p[5])

def p_elemento_arreglo_list(p):
    '''elemento_arreglo_list : elemento_arreglo_list SEPARADOR elemento_arreglo
                            | elemento_arreglo'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_elemento_arreglo(p):
    '''elemento_arreglo : numero
                       | CADENA
                       | ID
                       | expresion_concatenacion'''
    p[0] = p[1]

def p_acceso_arreglo(p):
    '''acceso_arreglo : ID CORCHETE_ABRIR NUMERO CORCHETE_CERRAR'''
    p[0] = AccesoArreglo(p[1], p[3])

# Tablas
def p_declaracion_tabla(p):
    '''declaracion_tabla : VAL ID ASIGNACION LLAVE_ABRIR par_clave_valor_list LLAVE_CERRAR'''
    p[0] = DeclaracionTabla(p[2], p[5])

def p_par_clave_valor_list(p):
    '''par_clave_valor_list : par_clave_valor_list SEPARADOR par_clave_valor
                           | par_clave_valor'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_par_clave_valor(p):
    '''par_clave_valor : CADENA ASIGNACION valor'''
    p[0] = (p[1], p[3])

def p_acceso_tabla(p):
    '''acceso_tabla : ID CORCHETE_ABRIR CADENA CORCHETE_CERRAR'''
    p[0] = AccesoTabla(p[1], p[3])

# Estructuras de control
def p_estructura_si(p):
    '''estructura_si : SI PAREN_ABRIR expresion PAREN_CERRAR LLAVE_ABRIR bloque_codigo LLAVE_CERRAR sinosis_opt'''
    p[0] = EstructuraSi(p[3], p[6], p[8])

def p_sinosis_opt(p):
    '''sinosis_opt : sinosis
                  | empty'''
    p[0] = p[1]

def p_sinosis(p):
    '''sinosis : SINOSI PAREN_ABRIR expresion PAREN_CERRAR LLAVE_ABRIR bloque_codigo LLAVE_CERRAR sinosis_opt
              | SINO LLAVE_ABRIR bloque_codigo LLAVE_CERRAR'''
    if len(p) == 5:
        p[0] = ('sino', p[3])
    else:
        p[0] = ('sinosi', p[3], p[6], p[8])

def p_estructura_mientras(p):
    '''estructura_mientras : MIENTRAS PAREN_ABRIR expresion PAREN_CERRAR LLAVE_ABRIR bloque_codigo LLAVE_CERRAR'''
    p[0] = EstructuraMientras(p[3], p[6])

def p_estructura_para(p):
    '''estructura_para : PARA PAREN_ABRIR VAL ID ASIGNACION expresion PUNTO_COMA expresion PUNTO_COMA expresion PAREN_CERRAR LLAVE_ABRIR bloque_codigo LLAVE_CERRAR'''
    init = DeclaracionVariable(p[4], p[6])
    p[0] = EstructuraPara(init, p[8], p[10], p[13])

def p_estructura_repetir(p):
    '''estructura_repetir : REPETIR LLAVE_ABRIR bloque_codigo LLAVE_CERRAR HASTA PAREN_ABRIR expresion PAREN_CERRAR'''
    p[0] = EstructuraRepetir(p[3], p[7])

def p_estructura_para_cada(p):
    '''estructura_para_cada : PARA PAREN_ABRIR ID EN ID PAREN_CERRAR LLAVE_ABRIR bloque_codigo LLAVE_CERRAR'''
    p[0] = ('para_cada', p[3], p[5], p[8])

def p_estructura_segun(p):
    '''estructura_segun : SEGUN PAREN_ABRIR expresion PAREN_CERRAR LLAVE_ABRIR casos caso_predeterminado_opt LLAVE_CERRAR'''
    p[0] = EstructuraSegun(p[3], p[6], p[7])

def p_casos(p):
    '''casos : casos caso
            | caso'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[2]]

def p_caso(p):
    '''caso : CASO valor CASE_LIMITADOR bloque_codigo PARAR'''
    p[0] = Caso(p[2], p[4])

def p_caso_predeterminado_opt(p):
    '''caso_predeterminado_opt : PREDETERMINADO CASE_LIMITADOR bloque_codigo
                              | empty'''
    if len(p) == 4:
        p[0] = p[3]
    else:
        p[0] = None

def p_estructura_intentar(p):
    '''estructura_intentar : INTENTAR LLAVE_ABRIR bloque_codigo LLAVE_CERRAR bloque_capturar bloque_finalmente_opt'''
    p[0] = ('intentar', p[3], p[5], p[6])

def p_bloque_capturar(p):
    '''bloque_capturar : CAPTURAR PAREN_ABRIR ID PAREN_CERRAR LLAVE_ABRIR bloque_codigo LLAVE_CERRAR'''
    p[0] = ('capturar', p[3], p[6])

def p_bloque_finalmente_opt(p):
    '''bloque_finalmente_opt : FINALMENTE LLAVE_ABRIR bloque_codigo LLAVE_CERRAR
                            | empty'''
    if len(p) == 5:
        p[0] = ('finalmente', p[3])
    else:
        p[0] = None

# Funciones
def p_declaracion_funcion(p):
    '''declaracion_funcion : FUN ID PAREN_ABRIR parametros_opt PAREN_CERRAR LLAVE_ABRIR bloque_codigo retorno_funcion_opt LLAVE_CERRAR'''
    p[0] = DeclaracionFuncion(p[2], p[4], p[7], p[8])

def p_parametros_opt(p):
    '''parametros_opt : parametros
                     | empty'''
    p[0] = p[1] if p[1] is not None else []

def p_parametros(p):
    '''parametros : parametros SEPARADOR ID
                 | ID'''
    if len(p) == 2:
        p[0] = [p[1]]
    else:
        p[0] = p[1] + [p[3]]

def p_retorno_funcion_opt(p):
    '''retorno_funcion_opt : RETORNAR expresion
                          | empty'''
    if len(p) == 3:
        p[0] = p[2]
    else:
        p[0] = None

def p_empty(p):
    '''empty :'''
    pass

def p_error(p):
    if p:
        raise SyntaxError(f"Error de sintaxis en el token '{p.value}' (línea {p.lineno})")
    else:
        raise SyntaxError("Error de sintaxis: final inesperado del archivo")

def crear_parser():
    return yacc.yacc()

def analizar_sintactico(codigo):
    try:
        lexer = crear_lexer()
        parser = crear_parser()
        
        ast = parser.parse(codigo, lexer=lexer)
        return ast, []
    except SyntaxError as e:
        return None, [str(e)]
    except Exception as e:
        return None, [f"Error inesperado: {str(e)}"]
