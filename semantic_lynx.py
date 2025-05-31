from typing import Dict, Optional, List, Any, TypedDict

class ResultadoAnalisisSemantico(TypedDict):
    errores: List[str]
    advertencias: List[str]
    tabla_simbolos: Dict[str, Any]


class Simbolo:
    def __init__(
        self,
        nombre: str,
        tipo: str,
        valor: Any = None,
        linea: Optional[int] = None,
        es_constante: bool = False,
        parametros: Optional[List[str]] = None,
        inicializado: bool = False,
        tipo_retorno: Optional[str] = None,
        usado: bool = False,
        declarado: bool = False,
    ):
        self.nombre = nombre
        self.tipo = tipo  # 'entero', 'flotante', 'cadena', 'arreglo', 'tabla', 'funcion', 'booleano'
        self.valor = valor
        self.linea = linea
        self.es_constante = es_constante
        self.parametros = parametros or []
        self.inicializado = inicializado
        self.tipo_retorno = tipo_retorno
        self.usado = usado
        self.declarado = declarado

    def to_dict(self):
        return {
            "nombre": self.nombre,
            "tipo": self.tipo,
            "valor": self.valor,
            "linea": self.linea,
            "es_constante": self.es_constante,
            "parametros": self.parametros,
            "tipo_retorno": self.tipo_retorno,
            "inicializado": self.inicializado,
            "usado": self.usado,
        }


class AnalizadorSemantico:
    def __init__(self):
        self.tabla_simbolos: Dict[str, Simbolo] = {}
        self.ambitos: List[Dict[str, Simbolo]] = [{}]  # Stack de ámbitos
        self.errores: List[str] = []
        self.advertencias: List[str] = []
        self.funciones_declaradas: Dict[str, Simbolo] = {}
        self.en_funcion = False
        self.tipo_retorno_esperado = None
        self.bucles_anidados = 0
        self.codigo_fuente = ""

    def error(self, mensaje: str, linea: Optional[int] = None):
        if linea:
            self.errores.append(f"Error semántico línea {linea}: {mensaje}")
        else:
            self.errores.append(f"Error semántico: {mensaje}")

    def advertencia(self, mensaje: str, linea: Optional[int] = None):
        if linea:
            self.advertencias.append(f"Advertencia línea {linea}: {mensaje}")
        else:
            self.advertencias.append(f"Advertencia: {mensaje}")

    def nuevo_ambito(self):
        """Crear un nuevo ámbito (scope)"""
        self.ambitos.append({})

    def cerrar_ambito(self):
        """Cerrar el ámbito actual"""
        if len(self.ambitos) > 1:
            # Verificar variables no utilizadas en el ámbito que se cierra
            ambito_actual = self.ambitos[-1]
            for simbolo in ambito_actual.values():
                if not simbolo.usado and simbolo.tipo != "funcion":
                    self.advertencia(
                        f"Variable '{simbolo.nombre}' declarada pero no utilizada",
                        simbolo.linea,
                    )
            self.ambitos.pop()

    def buscar_simbolo(self, nombre: str) -> Optional[Simbolo]:
        """Buscar un símbolo en todos los ámbitos, desde el más interno al más externo"""
        for ambito in reversed(self.ambitos):
            if nombre in ambito:
                simbolo = ambito[nombre]
                if not simbolo.declarado:
                    self.error(f"Variable '{nombre}' usada antes de ser declarada")
                return simbolo
        return None

    def declarar_simbolo(self, simbolo: Simbolo) -> bool:
        """Declarar un símbolo en el ámbito actual"""
        ambito_actual = self.ambitos[-1]

        # Verificar si ya existe en el ámbito actual
        if simbolo.nombre in ambito_actual:
            return False

        # Marcar como declarado y agregarlo al ámbito actual
        simbolo.declarado = True
        ambito_actual[simbolo.nombre] = simbolo
        # También agregarlo a la tabla global para el reporte final
        self.tabla_simbolos[simbolo.nombre] = simbolo
        return True

    def inferir_tipo(self, valor: Any) -> str:
        """Inferir el tipo de un valor"""
        if isinstance(valor, int):
            return "entero"
        elif isinstance(valor, float):
            return "flotante"
        elif isinstance(valor, str):
            return "cadena"
        elif isinstance(valor, bool):
            return "booleano"
        elif isinstance(valor, list):
            # Inferir tipo de elementos del arreglo si es posible
            if len(valor) > 0:
                tipo_elementos = {self.inferir_tipo(elem) for elem in valor}
                if len(tipo_elementos) == 1:
                    return f"arreglo<{tipo_elementos.pop()}>"
            return "arreglo<desconocido>"
        elif isinstance(valor, dict):
            return "tabla"
        else:
            return "desconocido"

    def tipos_compatibles(
        self, tipo1: str, tipo2: str, operacion: Optional[str] = None
    ) -> bool:
        """Determinar si dos tipos son compatibles para una operación"""
        # Si son del mismo tipo, siempre son compatibles
        if tipo1 == tipo2:
            return True

        # Para el operador +
        if operacion == "+":
            # Permitir concatenación si alguno es cadena
            if "cadena" in [tipo1, tipo2]:
                return True
            # Permitir operaciones entre números
            if tipo1 in ["entero", "flotante"] and tipo2 in ["entero", "flotante"]:
                return True
            return False

        # Para comparaciones (==, !=, <, >, <=, >=)
        if operacion in ["==", "!=", "<", ">", "<=", ">="]:
            # Permitir comparaciones entre tipos numéricos
            if tipo1 in ["entero", "flotante"] and tipo2 in ["entero", "flotante"]:
                return True
            # Permitir comparaciones con cadenas
            if "cadena" in [tipo1, tipo2]:
                return True
            return False

        # Para operaciones aritméticas
        if operacion in ["-", "*", "/", "%"]:
            return tipo1 in ["entero", "flotante"] and tipo2 in ["entero", "flotante"]

        return False

    def evaluar_expresion(self, nodo) -> tuple[str, Any]:
        """Evaluar una expresión y retornar su tipo y valor (si es posible)"""
        if nodo is None:
            return "nulo", None

        # Manejar literales
        if isinstance(nodo, str):
            return "cadena", nodo
        if isinstance(nodo, int):
            return "entero", nodo
        if isinstance(nodo, float):
            return "flotante", nodo
        if isinstance(nodo, bool):
            return "booleano", nodo

        # Nodos del AST
        if hasattr(nodo, "__class__"):
            clase = nodo.__class__.__name__

            if clase == "ExpresionBinaria":
                return self.evaluar_expresion_binaria(nodo)
            elif clase == "ExpresionUnaria":
                return self.evaluar_expresion_unaria(nodo)
            elif clase == "AccesoArreglo":
                return self.evaluar_acceso_arreglo(nodo)
            elif clase == "AccesoTabla":
                return self.evaluar_acceso_tabla(nodo)
            elif clase == "LlamadaFuncion":
                return self.evaluar_llamada_funcion(nodo)
            elif clase == "Identificador":
                return self.evaluar_identificador(nodo)

        # Si es un identificador como string
        if isinstance(nodo, str):
            simbolo = self.buscar_simbolo(nodo)
            if simbolo:
                simbolo.usado = True
                return simbolo.tipo, simbolo.valor
            else:
                self.error(f"Variable '{nodo}' no declarada")
                return "desconocido", None

        return "desconocido", None

    def evaluar_identificador(self, nodo) -> tuple[str, Any]:
        """Evaluar un identificador (variable)"""
        nombre = nodo.nombre
        simbolo = self.buscar_simbolo(nombre)
        print(
            f"evaluar_identificador: Nombre = {nombre}, Simbolo = {simbolo}"
        )  # Debug log

        if simbolo:
            if not simbolo.declarado:
                self.error(
                    f"Variable '{nombre}' usada antes de ser declarada", nodo.linea
                )
                return "desconocido", None
            simbolo.usado = True
            return simbolo.tipo, simbolo.valor
        else:
            self.error(f"Variable '{nombre}' no declarada", nodo.linea)
            return "desconocido", None

    def evaluar_llamada_funcion(self, nodo):
        """Evaluar llamada a función"""
        nombre_funcion = nodo.nombre if hasattr(nodo, "nombre") else str(nodo.funcion)

        # Verificar si la función existe
        simbolo = self.buscar_simbolo(nombre_funcion)
        if not simbolo:
            self.error(
                f"Función '{nombre_funcion}' no declarada", getattr(nodo, "linea", None)
            )
            return "desconocido", None

        if simbolo.tipo != "funcion":
            self.error(
                f"'{nombre_funcion}' no es una función", getattr(nodo, "linea", None)
            )
            return "desconocido", None

        simbolo.usado = True

        # Evaluar argumentos
        if hasattr(nodo, "argumentos"):
            for arg in nodo.argumentos:
                self.evaluar_expresion(arg)

        return simbolo.tipo_retorno or "nulo", None

    def evaluar_expresion_binaria(self, nodo) -> tuple[str, Any]:
        """Evaluar expresión binaria"""
        tipo_izq, val_izq = self.evaluar_expresion(nodo.izq)
        tipo_der, val_der = self.evaluar_expresion(nodo.der)
        operador = nodo.op

        # Para operador +
        if operador == "+":
            # Si alguno es cadena, el resultado es cadena
            if tipo_izq == "cadena" or tipo_der == "cadena":
                return "cadena", None
            # Si ambos son números
            if tipo_izq in ["entero", "flotante"] and tipo_der in [
                "entero",
                "flotante",
            ]:
                if tipo_izq == "flotante" or tipo_der == "flotante":
                    return "flotante", None
                return "entero", None
            # Si no es ninguno de los casos anteriores
            self.error(
                f"Tipos incompatibles para suma: {tipo_izq} + {tipo_der}", nodo.linea
            )
            return "desconocido", None

        # Para otros operadores aritméticos
        if operador in ["-", "*", "/", "%"]:
            if not (
                tipo_izq in ["entero", "flotante"]
                and tipo_der in ["entero", "flotante"]
            ):
                self.error(
                    f"Operador '{operador}' requiere operandos numéricos", nodo.linea
                )
                return "desconocido", None
            if tipo_izq == "flotante" or tipo_der == "flotante":
                return "flotante", None
            return "entero", None

        # Para operadores de comparación
        if operador in ["==", "!=", "<", ">", "<=", ">="]:
            # No emitir error en comparaciones entre cadenas y otros tipos
            return "booleano", None

        # Para operadores lógicos
        if operador in ["y", "o"]:
            if tipo_izq != "booleano":
                self.error(
                    f"Operando izquierdo de '{operador}' debe ser booleano", nodo.linea
                )
            if tipo_der != "booleano":
                self.error(
                    f"Operando derecho de '{operador}' debe ser booleano", nodo.linea
                )
            return "booleano", None

        return "desconocido", None

    def evaluar_expresion_unaria(self, nodo) -> tuple[str, Any]:
        """Evaluar expresión unaria"""
        tipo_expr, val_expr = self.evaluar_expresion(nodo.expr)
        operador = nodo.op
        linea = getattr(nodo, "linea", None)

        if operador in ["-", "+"]:
            # Eliminamos la verificación de tipos
            return tipo_expr, None
        elif operador == "no":
            if tipo_expr != "booleano":
                self.error(f"Operador 'no' requiere operando booleano", linea)
                return "desconocido", None
            return "booleano", None

        return "desconocido", None

    def evaluar_acceso_arreglo(self, nodo) -> tuple[str, Any]:
        """Evaluar acceso a arreglo"""
        nombre = nodo.nombre if hasattr(nodo, "nombre") else str(nodo.arreglo)
        simbolo = self.buscar_simbolo(nombre)
        linea = getattr(nodo, "linea", None)

        if not simbolo:
            self.error(f"Arreglo '{nombre}' no declarado", linea)
            return "desconocido", None

        if not simbolo.tipo.startswith("arreglo") and simbolo.tipo != "arreglo":
            self.error(f"'{nombre}' no es un arreglo", linea)
            return "desconocido", None

        simbolo.usado = True
        tipo_indice, valor_indice = self.evaluar_expresion(nodo.indice)

        if tipo_indice != "entero":
            self.error(f"El índice de arreglo debe ser entero", linea)
            return "desconocido", None

        # Si el arreglo tiene elementos, intentamos inferir el tipo
        if simbolo.valor and len(simbolo.valor) > 0:
            tipo_elemento = self.inferir_tipo(simbolo.valor[0])
            return tipo_elemento, None

        return "desconocido", None

    def evaluar_acceso_tabla(self, nodo) -> tuple[str, Any]:
        """Evaluar acceso a tabla"""
        nombre = nodo.nombre if hasattr(nodo, "nombre") else str(nodo.tabla)
        simbolo = self.buscar_simbolo(nombre)
        linea = getattr(nodo, "linea", None)

        if not simbolo:
            self.error(f"Tabla '{nombre}' no declarada", linea)
            return "desconocido", None

        if simbolo.tipo != "tabla":
            self.error(f"'{nombre}' no es una tabla", linea)
            return "desconocido", None

        simbolo.usado = True
        tipo_clave, _ = self.evaluar_expresion(nodo.clave)
        if tipo_clave != "cadena":
            self.error(f"Clave de tabla debe ser cadena", linea)

        return "desconocido", None

    def visitar_nodo(self, nodo):
        if nodo is None or isinstance(nodo, (str, int, float, bool)):
            return

        if isinstance(nodo, (list, tuple)):
            for item in nodo:
                self.visitar_nodo(item)
            return

        if not hasattr(nodo, "__class__"):
            return

        clase = nodo.__class__.__name__
        metodo = f"visitar_{clase}"

        if hasattr(self, metodo):
            getattr(self, metodo)(nodo)
        else:
            for attr_name, attr_value in nodo.__dict__.items():
                if attr_name != "linea":
                    self.visitar_nodo(attr_value)

    def visitar_Programa(self, nodo):
        """Visitar nodo Programa"""
        for instruccion in nodo.instrucciones:
            self.visitar_nodo(instruccion)

    def visitar_DeclaracionVariable(self, nodo):
        """Visitar declaración de variable"""
        tipo_valor = "nulo"
        valor = None

        if nodo.valor is not None:
            tipo_valor, valor = self.evaluar_expresion(nodo.valor)

        simbolo = Simbolo(
            nombre=nodo.nombre,
            tipo=tipo_valor,
            valor=valor,
            linea=nodo.linea,
            es_constante=False,
            declarado=True,  # Marcamos como declarada
        )

        if not self.declarar_simbolo(simbolo):
            self.error(
                f"Variable '{nodo.nombre}' ya declarada en este ámbito", nodo.linea
            )

    def visitar_AsignacionVariable(self, nodo):
        """Visitar asignación de variable"""
        print(f"Visitando asignación de variable: {nodo.nombre}")  # Debug log
        simbolo = self.buscar_simbolo(nodo.nombre)

        if not simbolo:
            self.error(f"Variable '{nodo.nombre}' no declarada", nodo.linea)
            return

        if not simbolo.declarado:
            self.error(
                f"Variable '{nodo.nombre}' usada antes de ser declarada", nodo.linea
            )
            return

        tipo_valor, valor = self.evaluar_expresion(nodo.valor)
        simbolo.tipo = tipo_valor
        simbolo.valor = valor
        simbolo.inicializado = True

    def visitar_DeclaracionArreglo(self, nodo):
        """Visitar declaración de arreglo"""
        elementos_tipos = []
        elementos_evaluados = []

        for elemento in nodo.elementos:
            tipo_elem, valor_elem = self.evaluar_expresion(elemento)
            elementos_tipos.append(tipo_elem)
            elementos_evaluados.append(valor_elem)

        # Verificar que todos los elementos sean del mismo tipo
        if elementos_tipos and len(set(elementos_tipos)) > 1:
            self.advertencia(
                f"Arreglo '{nodo.nombre}' contiene elementos de tipos diferentes",
                nodo.linea,
            )

        # Determinar el tipo del arreglo
        if elementos_tipos:
            tipo_elemento = elementos_tipos[0]
            tipo_arreglo = f"arreglo<{tipo_elemento}>"
        else:
            tipo_arreglo = "arreglo<desconocido>"

        simbolo = Simbolo(
            nombre=nodo.nombre,
            tipo=tipo_arreglo,
            valor=elementos_evaluados,
            linea=nodo.linea,
            es_constante=True,
        )

        if not self.declarar_simbolo(simbolo):
            self.error(
                f"Arreglo '{nodo.nombre}' ya declarado en este ámbito", nodo.linea
            )

    def visitar_DeclaracionTabla(self, nodo):
        """Visitar declaración de tabla"""
        tabla_valor = {}

        for clave, valor in nodo.pares:
            tipo_clave = self.inferir_tipo(clave)
            if tipo_clave != "cadena":
                self.error(f"Clave de tabla debe ser cadena", nodo.linea)

            tipo_valor, valor_evaluado = self.evaluar_expresion(valor)
            tabla_valor[clave] = valor_evaluado

        simbolo = Simbolo(
            nombre=nodo.nombre,
            tipo="tabla",
            valor=tabla_valor,
            linea=nodo.linea,
            es_constante=True,
        )

        if not self.declarar_simbolo(simbolo):
            self.error(f"Tabla '{nodo.nombre}' ya declarada en este ámbito", nodo.linea)

    def visitar_EstructuraSi(self, nodo):
        """Visitar estructura si"""
        tipo_condicion, _ = self.evaluar_expresion(nodo.condicion)
        if tipo_condicion != "booleano":
            self.error(f"Condición de 'si' debe ser booleana", nodo.linea)

        self.nuevo_ambito()
        self.visitar_nodo(nodo.bloque)
        self.cerrar_ambito()

        if hasattr(nodo, "sinosis") and nodo.sinosis:
            self.visitar_nodo(nodo.sinosis)

    def visitar_EstructuraMientras(self, nodo):
        """Visitar estructura mientras"""
        tipo_condicion, _ = self.evaluar_expresion(nodo.condicion)
        if tipo_condicion != "booleano":
            self.error(f"Condición de 'mientras' debe ser booleana", nodo.linea)

        self.bucles_anidados += 1
        self.nuevo_ambito()
        self.visitar_nodo(nodo.bloque)
        self.cerrar_ambito()
        self.bucles_anidados -= 1

    def visitar_EstructuraPara(self, nodo):
        """Visitar estructura para"""
        self.bucles_anidados += 1
        self.nuevo_ambito()

        # Declarar variable de inicialización
        self.visitar_nodo(nodo.init)

        # Verificar condición
        tipo_condicion, _ = self.evaluar_expresion(nodo.condicion)
        if tipo_condicion != "booleano":
            self.error(f"Condición de 'para' debe ser booleana", nodo.linea)

        # Verificar incremento
        self.evaluar_expresion(nodo.incremento)

        # Visitar bloque
        self.visitar_nodo(nodo.bloque)

        self.cerrar_ambito()
        self.bucles_anidados -= 1

    def visitar_EstructuraRepetir(self, nodo):
        """Visitar estructura repetir"""
        self.bucles_anidados += 1
        self.nuevo_ambito()
        self.visitar_nodo(nodo.bloque)
        self.cerrar_ambito()

        tipo_condicion, _ = self.evaluar_expresion(nodo.condicion)
        if tipo_condicion != "booleano":
            self.error(f"Condición de 'repetir-hasta' debe ser booleana", nodo.linea)

        self.bucles_anidados -= 1

    def visitar_DeclaracionFuncion(self, nodo):
        """Visitar declaración de función"""
        # Verificar que la función no esté ya declarada
        if nodo.nombre in self.funciones_declaradas:
            self.error(f"Función '{nodo.nombre}' ya declarada", nodo.linea)
            return

        simbolo = Simbolo(
            nombre=nodo.nombre,
            tipo="funcion",
            parametros=nodo.parametros,
            tipo_retorno=(
                "nulo"
                if not hasattr(nodo, "retorno") or nodo.retorno is None
                else "desconocido"
            ),
            linea=nodo.linea,
        )

        self.funciones_declaradas[nodo.nombre] = simbolo
        self.declarar_simbolo(simbolo)

        # Analizar cuerpo de la función
        self.nuevo_ambito()
        self.en_funcion = True
        anterior_tipo_retorno = self.tipo_retorno_esperado

        # Declarar parámetros en el ámbito de la función
        for param in nodo.parametros:
            param_simbolo = Simbolo(
                nombre=param,
                tipo="desconocido",  # Tipo inferido en uso
                linea=nodo.linea,
            )
            self.declarar_simbolo(param_simbolo)

        # Visitar bloque de la función
        self.visitar_nodo(nodo.bloque)

        # Verificar retorno si existe
        if hasattr(nodo, "retorno") and nodo.retorno:
            tipo_retorno, _ = self.evaluar_expresion(nodo.retorno)
            simbolo.tipo_retorno = tipo_retorno

        self.tipo_retorno_esperado = anterior_tipo_retorno
        self.en_funcion = False
        self.cerrar_ambito()

    def visitar_Imprimir(self, nodo):
        """Visitar instrucción imprimir"""
        for elemento in nodo.elementos:
            self.evaluar_expresion(elemento)

    def visitar_ExpresionBinaria(self, nodo):
        """Visitar expresión binaria"""
        self.evaluar_expresion_binaria(nodo)

    def visitar_ExpresionUnaria(self, nodo):
        """Visitar expresión unaria"""
        self.evaluar_expresion_unaria(nodo)

    def visitar_AccesoArreglo(self, nodo):
        """Visitar acceso a arreglo"""
        nombre = nodo.nombre if hasattr(nodo, "nombre") else str(nodo.arreglo)
        simbolo = self.buscar_simbolo(nombre)
        linea = getattr(nodo, "linea", None)

        if not simbolo:
            self.error(f"Arreglo '{nombre}' no declarado", linea)
            return

        if not simbolo.tipo.startswith("arreglo") and simbolo.tipo != "arreglo":
            self.error(f"'{nombre}' no es un arreglo", linea)
            return

        simbolo.usado = True
        tipo_indice, valor_indice = self.evaluar_expresion(nodo.indice)

        if tipo_indice != "entero":
            self.error(f"El índice de arreglo debe ser entero", linea)
            return

    def visitar_AccesoTabla(self, nodo):
        """Visitar acceso a tabla"""
        nombre = nodo.nombre if hasattr(nodo, "nombre") else str(nodo.tabla)
        simbolo = self.buscar_simbolo(nombre)
        linea = getattr(nodo, "linea", None)

        if not simbolo:
            self.error(f"Tabla '{nombre}' no declarada", linea)
            return

        if simbolo.tipo != "tabla":
            self.error(f"'{nombre}' no es una tabla", linea)
            return

        simbolo.usado = True
        tipo_clave, _ = self.evaluar_expresion(nodo.clave)
        if tipo_clave != "cadena":
            self.error(f"Clave de tabla debe ser cadena", linea)

    def analizar(self, ast, codigo: str = "") -> ResultadoAnalisisSemantico:
        """Realizar análisis semántico completo"""
        self.codigo_fuente = codigo
        self.errores = []
        self.advertencias = []
        self.tabla_simbolos = {}
        self.ambitos = [{}]
        self.funciones_declaradas = {}

        try:
            self.visitar_nodo(ast)

            # Verificaciones finales
            self.verificaciones_finales()

        except Exception as e:
            self.error(f"Error interno en análisis semántico: {str(e)}")

        # Convertir tabla de símbolos a formato serializable
        tabla_serializable = {}
        for nombre, simbolo in self.tabla_simbolos.items():
            tabla_serializable[nombre] = simbolo.to_dict()

        return {
            "errores": self.errores,
            "advertencias": self.advertencias,
            "tabla_simbolos": tabla_serializable,
        }

    def verificaciones_finales(self):
        """Realizar verificaciones finales"""
        # Verificar variables no utilizadas
        for simbolo in self.tabla_simbolos.values():
            if not simbolo.usado and simbolo.tipo != "funcion":
                self.advertencia(
                    f"Variable '{simbolo.nombre}' declarada pero no utilizada",
                    simbolo.linea,
                )

        # Verificar funciones declaradas pero no utilizadas
        for simbolo in self.funciones_declaradas.values():
            if not simbolo.usado:
                self.advertencia(
                    f"Función '{simbolo.nombre}' declarada pero no utilizada",
                    simbolo.linea,
                )


# Funciones de utilidad para integración
def crear_analizador_semantico():
    """Crear una nueva instancia del analizador semántico"""
    return AnalizadorSemantico()
