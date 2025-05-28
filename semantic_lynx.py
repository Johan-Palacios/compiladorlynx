from collections import defaultdict
from parser_lynx import *

class TablaSimbolos:
    def __init__(self):
        self.tabla = defaultdict(dict)  # Ámbito global
        self.ambitos = [self.tabla]  # Lista de ámbitos (para funciones o bloques)

    def entrar_ambito(self):
        nuevo_ambito = defaultdict(dict)
        self.ambitos.append(nuevo_ambito)
        return nuevo_ambito

    def salir_ambito(self):
        self.ambitos.pop()

    def declarar_variable(self, nombre, tipo=None, inicializada=False, linea=None):
        ambito_actual = self.ambitos[-1]
        if nombre in ambito_actual:
            return f"Error semántico: Variable '{nombre}' ya declarada en la línea {linea}"
        ambito_actual[nombre] = {'tipo': tipo, 'inicializada': inicializada, 'linea': linea}
        return None

    def usar_variable(self, nombre, linea):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                if not ambito[nombre]['inicializada']:
                    return f"Error semántico: Variable '{nombre}' usada antes de inicializarse en la línea {linea}"
                return ambito[nombre]['tipo']
        return f"Error semántico: Variable '{nombre}' no declarada en la línea {linea}"

    def declarar_funcion(self, nombre, parametros, tipo_retorno=None, linea=None):
        ambito_global = self.ambitos[0]
        if nombre in ambito_global:
            return f"Error semántico: Función '{nombre}' ya declarada en la línea {linea}"
        ambito_global[nombre] = {'tipo': 'funcion', 'parametros': parametros, 'tipo_retorno': tipo_retorno, 'linea': linea}
        return None

    def usar_funcion(self, nombre, num_args, linea):
        ambito_global = self.ambitos[0]
        if nombre not in ambito_global or ambito_global[nombre]['tipo'] != 'funcion':
            return f"Error semántico: Función '{nombre}' no declarada en la línea {linea}"
        if len(ambito_global[nombre]['parametros']) != num_args:
            return f"Error semántico: La función '{nombre}' espera {len(ambito_global[nombre]['parametros'])} argumentos, pero se proporcionaron {num_args} en la línea {linea}"
        return ambito_global[nombre]['tipo_retorno']

class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()
        self.errores = []
        self.current_line = 1  # Para rastrear la línea actual

    def analizar(self, ast, codigo):
        if ast is None:
            self.errores.append("Error: AST no generado")
            return self.errores
        # Dividir el código en líneas para rastrear números de línea
        self.lineas = codigo.split('\n')
        self.visitar(ast)
        return self.errores

    def visitar(self, nodo, linea=None):
        if isinstance(nodo, Programa):
            for instruccion in nodo.instrucciones:
                self.visitar(instruccion, linea=self.current_line)
                self.current_line += str(instruccion).count('\n') + 1

        elif isinstance(nodo, DeclaracionVariable):
            tipo = self.inferir_tipo(nodo.valor) if nodo.valor else None
            error = self.tabla_simbolos.declarar_variable(nodo.nombre, tipo=tipo, inicializada=nodo.valor is not None, linea=linea)
            if error:
                self.errores.append(error)
            if nodo.valor:
                self.visitar(nodo.valor, linea)

        elif isinstance(nodo, AsignacionVariable):
            tipo_var = self.tabla_simbolos.usar_variable(nodo.nombre, linea)
            if isinstance(tipo_var, str):  # Error
                self.errores.append(tipo_var)
            else:
                tipo_valor = self.inferir_tipo(nodo.valor)
                if tipo_var and tipo_valor and tipo_var != tipo_valor:
                    self.errores.append(f"Error semántico: Asignación de tipo '{tipo_valor}' a variable de tipo '{tipo_var}' en la línea {linea}")
                self.visitar(nodo.valor, linea)

        elif isinstance(nodo, DeclaracionArreglo):
            error = self.tabla_simbolos.declarar_variable(nodo.nombre, tipo='arreglo', inicializada=True, linea=linea)
            if error:
                self.errores.append(error)
            for elemento in nodo.elementos:
                tipo_elem = self.inferir_tipo(elemento)
                if tipo_elem not in ['cadena', 'entero', 'flotante']:
                    self.errores.append(f"Error semántico: Elemento de arreglo de tipo '{tipo_elem}' no soportado en la línea {linea}")
                self.visitar(elemento, linea)

        elif isinstance(nodo, EstructuraSi):
            self.visitar(nodo.condicion, linea)
            tipo_cond = self.inferir_tipo(nodo.condicion)
            if tipo_cond not in ['entero', 'flotante', 'cadena', None]:
                self.errores.append(f"Error semántico: Condición de 'si' debe ser una expresión lógica, no '{tipo_cond}' en la línea {linea}")
            self.tabla_simbolos.entrar_ambito()
            for instruccion in nodo.bloque:
                self.visitar(instruccion, linea)
            self.tabla_simbolos.salir_ambito()
            if nodo.sinosis:
                for sinosi in nodo.sinosis:
                    if sinosi[0] == 'sinosi':
                        self.visitar(sinosi[1], linea)  # Condición
                        tipo_cond = self.inferir_tipo(sinosi[1])
                        if tipo_cond not in ['entero', 'flotante', 'cadena', None]:
                            self.errores.append(f"Error semántico: Condición de 'sinosi' debe ser una expresión lógica, no '{tipo_cond}' en la línea {linea}")
                        self.tabla_simbolos.entrar_ambito()
                        for instruccion in sinosi[2]:
                            self.visitar(instruccion, linea)
                        self.tabla_simbolos.salir_ambito()
                    else:  # sino
                        self.tabla_simbolos.entrar_ambito()
                        for instruccion in sinosi[1]:
                            self.visitar(instruccion, linea)
                        self.tabla_simbolos.salir_ambito()

        elif isinstance(nodo, EstructuraMientras):
            self.visitar(nodo.condicion, linea)
            tipo_cond = self.inferir_tipo(nodo.condicion)
            if tipo_cond not in ['entero', 'flotante', 'cadena', None]:
                self.errores.append(f"Error semántico: Condición de 'mientras' debe ser una expresión lógica, no '{tipo_cond}' en la línea {linea}")
            self.tabla_simbolos.entrar_ambito()
            for instruccion in nodo.bloque:
                self.visitar(instruccion, linea)
            self.tabla_simbolos.salir_ambito()

        elif isinstance(nodo, DeclaracionFuncion):
            error = self.tabla_simbolos.declarar_funcion(nodo.nombre, nodo.parametros, tipo_retorno=None, linea=linea)
            if error:
                self.errores.append(error)
            self.tabla_simbolos.entrar_ambito()
            for param in nodo.parametros:
                self.tabla_simbolos.declarar_variable(param, tipo=None, inicializada=True, linea=linea)
            for instruccion in nodo.bloque:
                self.visitar(instruccion, linea)
            if nodo.retorno:
                self.visitar(nodo.retorno, linea)
            self.tabla_simbolos.salir_ambito()

        elif isinstance(nodo, Imprimir):
            for elemento in nodo.elementos:
                self.visitar(elemento, linea)

        elif isinstance(nodo, ExpresionBinaria):
            tipo_izq = self.visitar(nodo.izq, linea)
            tipo_der = self.visitar(nodo.der, linea)
            if nodo.op in ['+', '-', '*', '/', '%']:
                if not self.tipos_compatible_aritmetica(tipo_izq, tipo_der):
                    self.errores.append(f"Error semántico: Tipos incompatibles '{tipo_izq}' y '{tipo_der}' para operación '{nodo.op}' en la línea {linea}")
            elif nodo.op in ['==', '!=', '<', '>', '<=', '>=']:
                if not self.tipos_compatible_comparacion(tipo_izq, tipo_der):
                    self.errores.append(f"Error semántico: Tipos incompatibles '{tipo_izq}' y '{tipo_der}' para comparación '{nodo.op}' en la línea {linea}")
            elif nodo.op in ['y', 'o']:
                if tipo_izq not in ['entero', 'flotante', 'cadena', None] or tipo_der not in ['entero', 'flotante', 'cadena', None]:
                    self.errores.append(f"Error semántico: Tipos incompatibles '{tipo_izq}' y '{tipo_der}' para operación lógica '{nodo.op}' en la línea {linea}")
            return self.inferir_tipo(nodo)

        elif isinstance(nodo, AccesoArreglo):
            tipo = self.tabla_simbolos.usar_variable(nodo.nombre, linea)
            if isinstance(tipo, str):  # Error
                self.errores.append(tipo)
            elif tipo != 'arreglo':
                self.errores.append(f"Error semántico: '{nodo.nombre}' no es un arreglo en la línea {linea}")
            tipo_indice = self.inferir_tipo(nodo.indice)
            if tipo_indice != 'entero':
                self.errores.append(f"Error semántico: El índice del arreglo debe ser de tipo 'entero', no '{tipo_indice}' en la línea {linea}")
            self.visitar(nodo.indice, linea)
            return 'entero'  # Suponiendo que los elementos del arreglo son de tipo homogéneo

        elif isinstance(nodo, str):
            return 'cadena'
        elif isinstance(nodo, int):
            return 'entero'
        elif isinstance(nodo, float):
            return 'flotante'
        elif isinstance(nodo, list):
            for elemento in nodo:
                self.visitar(elemento, linea)
            return 'arreglo'
        elif nodo is None:
            return None
        else:
            raise ValueError(f"Tipo de nodo no soportado: {type(nodo)} en la línea {linea}")

    def inferir_tipo(self, valor):
        if isinstance(valor, str):
            return 'cadena'
        elif isinstance(valor, int):
            return 'entero'
        elif isinstance(valor, float):
            return 'flotante'
        elif isinstance(valor, list):
            return 'arreglo'
        elif isinstance(valor, ExpresionBinaria):
            tipo_izq = self.inferir_tipo(valor.izq)
            tipo_der = self.inferir_tipo(valor.der)
            if valor.op == '+':
                if tipo_izq == 'cadena' or tipo_der == 'cadena':
                    return 'cadena'
                return 'entero' if tipo_izq == 'entero' and tipo_der == 'entero' else 'flotante'
            elif valor.op in ['-', '*', '/', '%']:
                return 'entero' if tipo_izq == 'entero' and tipo_der == 'entero' else 'flotante'
            elif valor.op in ['==', '!=', '<', '>', '<=', '>=', 'y', 'o']:
                return 'entero'  # Resultado de comparaciones y lógicas es entero (0 o 1)
        elif isinstance(valor, AccesoArreglo):
            return 'entero'  # Suponiendo tipo homogéneo para elementos de arreglos
        return None

    def tipos_compatible_aritmetica(self, tipo1, tipo2):
        return tipo1 in ['entero', 'flotante', None] and tipo2 in ['entero', 'flotante', None]

    def tipos_compatible_comparacion(self, tipo1, tipo2):
        if tipo1 == 'arreglo' or tipo2 == 'arreglo':
            return False
        return tipo1 in ['cadena', 'entero', 'flotante', None] and tipo2 in ['cadena', 'entero', 'flotante', None]
