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

    def declarar_variable(self, nombre, tipo=None, inicializada=False):
        ambito_actual = self.ambitos[-1]
        if nombre in ambito_actual:
            return f"Error semántico: Variable '{nombre}' ya declarada en este ámbito"
        ambito_actual[nombre] = {'tipo': tipo, 'inicializada': inicializada}
        return None

    def usar_variable(self, nombre, linea):
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                if not ambito[nombre]['inicializada']:
                    return f"Error semántico: Variable '{nombre}' usada antes de inicializarse en línea {linea}"
                return ambito[nombre]['tipo']
        return f"Error semántico: Variable '{nombre}' no declarada en línea {linea}"

    def declarar_funcion(self, nombre, parametros, tipo_retorno=None):
        ambito_global = self.ambitos[0]
        if nombre in ambito_global:
            return f"Error semántico: Función '{nombre}' ya declarada"
        ambito_global[nombre] = {'tipo': 'funcion', 'parametros': parametros, 'tipo_retorno': tipo_retorno}
        return None

    def usar_funcion(self, nombre, linea):
        ambito_global = self.ambitos[0]
        if nombre not in ambito_global or ambito_global[nombre]['tipo'] != 'funcion':
            return f"Error semántico: Función '{nombre}' no declarada en línea {linea}"
        return ambito_global[nombre]

class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos = TablaSimbolos()
        self.errores = []

    def analizar(self, ast):
        if ast is None:
            self.errores.append("Error: AST no generado")
            return self.errores
        self.visitar(ast)
        return self.errores

    def visitar(self, nodo):
        if isinstance(nodo, Programa):
            for instruccion in nodo.instrucciones:
                self.visitar(instruccion)

        elif isinstance(nodo, DeclaracionVariable):
            error = self.tabla_simbolos.declarar_variable(nodo.nombre, tipo=self.inferir_tipo(nodo.valor), inicializada=nodo.valor is not None)
            if error:
                self.errores.append(error)
            if nodo.valor:
                self.visitar(nodo.valor)

        elif isinstance(nodo, AsignacionVariable):
            tipo = self.tabla_simbolos.usar_variable(nodo.nombre, 0)  # Línea 0 para simplificar; usar línea real si está disponible
            if isinstance(tipo, str):  # Error
                self.errores.append(tipo)
            self.visitar(nodo.valor)

        elif isinstance(nodo, DeclaracionArreglo):
            error = self.tabla_simbolos.declarar_variable(nodo.nombre, tipo='arreglo', inicializada=True)
            if error:
                self.errores.append(error)
            for elemento in nodo.elementos:
                self.visitar(elemento)

        elif isinstance(nodo, EstructuraSi):
            self.visitar(nodo.condicion)
            self.tabla_simbolos.entrar_ambito()
            for instruccion in nodo.bloque:
                self.visitar(instruccion)
            self.tabla_simbolos.salir_ambito()
            if nodo.sinosis:
                for sinosi in nodo.sinosis:
                    if sinosi[0] == 'sinosi':
                        self.visitar(sinosi[1])  # Condición
                        self.tabla_simbolos.entrar_ambito()
                        for instruccion in sinosi[2]:
                            self.visitar(instruccion)
                        self.tabla_simbolos.salir_ambito()
                    else:  # sino
                        self.tabla_simbolos.entrar_ambito()
                        for instruccion in sinosi[1]:
                            self.visitar(instruccion)
                        self.tabla_simbolos.salir_ambito()

        elif isinstance(nodo, EstructuraMientras):
            self.visitar(nodo.condicion)
            self.tabla_simbolos.entrar_ambito()
            for instruccion in nodo.bloque:
                self.visitar(instruccion)
            self.tabla_simbolos.salir_ambito()

        elif isinstance(nodo, DeclaracionFuncion):
            error = self.tabla_simbolos.declarar_funcion(nodo.nombre, nodo.parametros, tipo_retorno=None)
            if error:
                self.errores.append(error)
            self.tabla_simbolos.entrar_ambito()
            for param in nodo.parametros:
                self.tabla_simbolos.declarar_variable(param, tipo=None, inicializada=True)
            for instruccion in nodo.bloque:
                self.visitar(instruccion)
            if nodo.retorno:
                self.visitar(nodo.retorno)
            self.tabla_simbolos.salir_ambito()

        elif isinstance(nodo, Imprimir):
            for elemento in nodo.elementos:
                self.visitar(elemento)

        elif isinstance(nodo, ExpresionBinaria):
            if nodo.op == '+':
                tipo_izq = self.visitar(nodo.izq)
                tipo_der = self.visitar(nodo.der)
                if not self.tipos_compatible_concatenacion(tipo_izq, tipo_der):
                    self.errores.append(f"Error semántico: Tipos incompatibles en concatenación en línea desconocida")
            else:
                self.visitar(nodo.izq)
                self.visitar(nodo.der)

        elif isinstance(nodo, AccesoArreglo):
            tipo = self.tabla_simbolos.usar_variable(nodo.nombre, 0)
            if isinstance(tipo, str):  # Error
                self.errores.append(tipo)
            elif tipo != 'arreglo':
                self.errores.append(f"Error semántico: '{nodo.nombre}' no es un arreglo en línea desconocida")
            self.visitar(nodo.indice)

        elif isinstance(nodo, str):
            return 'cadena'
        elif isinstance(nodo, int):
            return 'entero'
        elif isinstance(nodo, float):
            return 'flotante'
        elif isinstance(nodo, list):
            for elemento in nodo:
                self.visitar(elemento)
        elif nodo is None:
            pass
        else:
            raise ValueError(f"Tipo de nodo no soportado: {type(nodo)}")

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
            if valor.op == '+':
                tipo_izq = self.inferir_tipo(valor.izq)
                tipo_der = self.inferir_tipo(valor.der)
                if tipo_izq == 'cadena' or tipo_der == 'cadena':
                    return 'cadena'
                return 'entero' if tipo_izq == 'entero' and tipo_der == 'entero' else 'flotante'
        return None

    def tipos_compatible_concatenacion(self, tipo1, tipo2):
        return (tipo1 in ['cadena', 'entero', 'flotante', None] and
                tipo2 in ['cadena', 'entero', 'flotante', None])
