from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Union
import traceback

# Importar nuestros analizadores
from lexer_lynx import analizar_lexico
from parser_lynx import analizar_sintactico
from semantic_lynx import AnalizadorSemantico

app = FastAPI(title="Analizador Lynx", version="1.0.0")

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4321", "http://localhost:3000", "http://localhost:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos Pydantic
class CodigoRequest(BaseModel):
    codigo: str

class Token(BaseModel):
    lexema: str
    tipo: str
    linea: int
    columna: int

class AnalisisResponse(BaseModel):
    tokens: List[Token]
    errores: List[str]
    ast: Optional[Dict[str, Any]] = None
    exito: bool

class AnalisisSintacticoResponse(BaseModel):
    ast: Optional[Dict[str, Any]]
    errores: List[str]
    exito: bool

class AnalisisLexicoResponse(BaseModel):
    tokens: List[Token]
    errores: List[str]
    exito: bool

class AnalisisSemanticoResponse(BaseModel):
    errores: List[str]
    exito: bool

def ast_to_dict(node) -> Optional[Dict[str, Any]]:
    if node is None:
        return None
    if isinstance(node, (str, int, float, bool)):
        return {"valor": node, "tipo_primitivo": type(node).__name__}
    if isinstance(node, list):
        return {"tipo": "lista", "elementos": [ast_to_dict(item) for item in node]}
    if isinstance(node, tuple):
        return {"tipo": "tupla", "elementos": [ast_to_dict(item) for item in node]}
    if hasattr(node, '__dict__'):
        result = {'tipo': node.__class__.__name__, 'linea': node.linea}
        for key, value in node.__dict__.items():
            if key == 'linea':
                continue
            if isinstance(value, (str, int, float, bool)):
                result[key] = {"valor": value, "tipo_primitivo": type(value).__name__}
            elif isinstance(value, (list, tuple)):
                result[key] = ast_to_dict(value)
            elif hasattr(value, '__dict__'):
                result[key] = ast_to_dict(value)
            elif value is None:
                result[key] = None
            else:
                result[key] = {"valor": str(value), "tipo_primitivo": "string"}
        return result
    return {"valor": str(node), "tipo_primitivo": "string"}

@app.get("/")
async def root():
    return {"mensaje": "Analizador Lynx API funcionando correctamente"}

@app.get("/health")
async def health_check():
    return {"status": "ok", "servicio": "Analizador Lynx"}

@app.post("/analizar", response_model=AnalisisResponse)
async def analizar_codigo(request: CodigoRequest):
    try:
        if not request.codigo.strip():
            return AnalisisResponse(
                tokens=[],
                errores=["El código no puede estar vacío"],
                ast=None,
                exito=False
            )
        
        tokens_data, errores_lexicos = analizar_lexico(request.codigo)
        tokens = [Token(**token_data) for token_data in tokens_data]
        errores_totales = errores_lexicos.copy()
        ast_dict = None
        
        if not errores_lexicos:
            try:
                ast, errores_sintacticos = analizar_sintactico(request.codigo)
                errores_totales.extend(errores_sintacticos)
                if ast is not None:
                    ast_dict = ast_to_dict(ast)
            except Exception as e:
                errores_totales.append(f"Error en análisis sintáctico: {str(e)}")
                print(f"Error sintáctico detallado: {traceback.format_exc()}")
        
        return AnalisisResponse(
            tokens=tokens,
            errores=errores_totales,
            ast=ast_dict,
            exito=len(errores_totales) == 0
        )
        
    except Exception as e:
        print(f"Error general: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500, 
            detail=f"Error interno del servidor: {str(e)}"
        )

@app.post("/analizar-lexico", response_model=AnalisisLexicoResponse)
async def analizar_solo_lexico(request: CodigoRequest):
    try:
        if not request.codigo.strip():
            return AnalisisLexicoResponse(
                tokens=[],
                errores=["El código no puede estar vacío"],
                exito=False
            )
        
        tokens_data, errores = analizar_lexico(request.codigo)
        tokens = [Token(**token_data) for token_data in tokens_data]
        
        return AnalisisLexicoResponse(
            tokens=tokens,
            errores=errores,
            exito=len(errores) == 0
        )
        
    except Exception as e:
        print(f"Error en análisis léxico: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en análisis léxico: {str(e)}"
        )

@app.post("/analizar-sintactico", response_model=AnalisisSintacticoResponse)
async def analizar_solo_sintactico(request: CodigoRequest):
    try:
        if not request.codigo.strip():
            return AnalisisSintacticoResponse(
                ast=None,
                errores=["El código no puede estar vacío"],
                exito=False
            )
        
        _, errores_lexicos = analizar_lexico(request.codigo)
        if errores_lexicos:
            return AnalisisSintacticoResponse(
                ast=None,
                errores=["No se puede realizar análisis sintáctico: existen errores léxicos"] + errores_lexicos,
                exito=False
            )
        
        ast, errores_sintacticos = analizar_sintactico(request.codigo)
        ast_dict = ast_to_dict(ast) if ast is not None else None
        
        return AnalisisSintacticoResponse(
            ast=ast_dict,
            errores=errores_sintacticos,
            exito=len(errores_sintacticos) == 0
        )
        
    except Exception as e:
        print(f"Error en análisis sintáctico: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en análisis sintáctico: {str(e)}"
        )

@app.post("/analizar-semantico", response_model=AnalisisSemanticoResponse)
async def analizar_solo_semantico(request: CodigoRequest):
    try:
        if not request.codigo.strip():
            return AnalisisSemanticoResponse(
                errores=["El código no puede estar vacío"],
                exito=False
            )
        
        # Verificar análisis léxico
        _, errores_lexicos = analizar_lexico(request.codigo)
        if errores_lexicos:
            return AnalisisSemanticoResponse(
                errores=["No se puede realizar análisis semántico: existen errores léxicos"] + errores_lexicos,
                exito=False
            )
        
        # Verificar análisis sintáctico
        ast, errores_sintacticos = analizar_sintactico(request.codigo)
        if errores_sintacticos:
            return AnalisisSemanticoResponse(
                errores=["No se puede realizar análisis semántico: existen errores sintácticos"] + errores_sintacticos,
                exito=False
            )
        
        # Análisis semántico
        analizador = AnalizadorSemantico()
        errores_semanticos = analizador.analizar(ast, request.codigo)
        
        return AnalisisSemanticoResponse(
            errores=errores_semanticos,
            exito=len(errores_semanticos) == 0
        )
        
    except Exception as e:
        print(f"Error en análisis semántico: {traceback.format_exc()}")
        raise HTTPException(
            status_code=500,
            detail=f"Error en análisis semántico: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    print("Iniciando servidor FastAPI para Analizador Lynx...")
    print("Documentación disponible en: http://localhost:8000/docs")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
