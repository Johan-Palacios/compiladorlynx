import { useState, useRef, useEffect, useCallback } from 'react';
import { Editor } from '@monaco-editor/react';
import { AlertCircle, CheckCircle, Code, Play, FileText, Zap, TreePine, Settings, Lightbulb, Download, Upload, Copy, RotateCcw, Brain } from 'lucide-react';

export default function LynxEditorMejorado() {
  const [codigo, setCodigo] = useState(`// Ejemplo completo de Lynx
val mensaje = "Bienvenido a Lynx"
imprimir(mensaje)

// Variables y operaciones
val x = 10
val a = 20
val suma = x + a

si (suma > 25) {
  imprimir("La suma es mayor a 25:", suma)
} sinosi (suma == 25) {
  imprimir("La suma es exactamente 25")
} sino {
  imprimir("La suma es menor a 25:", suma)
}

// Bucles
mientras (x < 15) {
  imprimir("x es:", x)
  x = x + 1
}

// Arreglos
val colores = ["rojo", "verde", "azul"]
imprimir("Mi color favorito es:", colores[1])

// Funciones
fun saludar(nombre) {
  imprimir("¡Hola", nombre + "!")
  retornar "Saludo completado"
}`);

  const [tokens, setTokens] = useState([]);
  const [errores, setErrores] = useState([]);
  const [warnings, setWarnings] = useState([]);
  const [ast, setAst] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [validacionTiempoReal, setValidacionTiempoReal] = useState(true);
  const [variablesDeclaradas, setVariablesDeclaradas] = useState(new Set());
  const [funcionesDeclaradas, setFuncionesDeclaradas] = useState(new Set());
  const [estadoConexion, setEstadoConexion] = useState('desconocido');
  const [resultado, setResultado] = useState('');
  const [mostrarAST, setMostrarAST] = useState(false);

  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  const validationTimeoutRef = useRef(null);

  const palabrasReservadas = [
    'val', 'si', 'sino', 'sinosi', 'mientras', 'para', 'fun', 'retornar',
    'imprimir', 'verdadero', 'falso', 'nulo', 'y', 'o', 'no', 'hacer',
    'salir', 'en', 'repetir', 'hasta', 'intentar', 'capturar', 'segun',
    'caso', 'predeterminado', 'finalmente', 'parar'
  ];

  const funcionesBuiltIn = [
    'imprimir', 'leer', 'longitud', 'tipo', 'convertir', 'redondear',
    'absoluto', 'maximo', 'minimo', 'aleatorio'
  ];

  const verificarConexion = useCallback(async () => {
    try {
      const response = await fetch('http://localhost:8000/health');
      if (response.ok) {
        setEstadoConexion('conectado');
      } else {
        setEstadoConexion('error');
      }
    } catch (error) {
      setEstadoConexion('desconectado');
    }
  }, []);

  useEffect(() => {
    verificarConexion();
    const interval = setInterval(verificarConexion, 30000);
    return () => clearInterval(interval);
  }, [verificarConexion]);

  const extraerSimbolos = useCallback((codigoTexto) => {
    const variables = new Set();
    const funciones = new Set();

    const regexVar = /val\s+([a-zA-Z_][a-zA-Z0-9_]*)/g;
    let match;
    while ((match = regexVar.exec(codigoTexto)) !== null) {
      variables.add(match[1]);
    }

    const regexFun = /fun\s+([a-zA-Z_][a-zA-Z0-9_]*)/g;
    while ((match = regexFun.exec(codigoTexto)) !== null) {
      funciones.add(match[1]);
    }

    setVariablesDeclaradas(variables);
    setFuncionesDeclaradas(funciones);
  }, []);

  const configurarLynxAvanzado = useCallback((monaco) => {
    if (!monaco.languages.getLanguages().find(lang => lang.id === 'lynx')) {
      monaco.languages.register({ id: 'lynx' });
    }

    monaco.languages.setMonarchTokensProvider('lynx', {
      defaultToken: 'invalid',
      keywords: palabrasReservadas,
      builtins: funcionesBuiltIn,
      tokenizer: {
        root: [
          [/\/\/.*$/, 'comment'],
          [/\/\*/, 'comment', '@comment'],
          [/\b(?:val|si|sino|sinosi|mientras|para|fun|retornar|imprimir|verdadero|falso|nulo|y|o|no|hacer|salir|en|repetir|hasta|intentar|capturar|segun|caso|predeterminado|finalmente|parar)\b/, 'keyword'],
          [/\b(?:imprimir|leer|longitud|tipo|convertir|redondear|absoluto|maximo|minimo|aleatorio)\b/, 'predefined'],
          [/\d*\.\d+([eE][\-+]?\d+)?/, 'number.float'],
          [/0[xX][0-9a-fA-F]+/, 'number.hex'],
          [/\d+/, 'number'],
          [/"([^"\\]|\\.)*$/, 'string.invalid'],
          [/"/, 'string', '@string'],
          [/'([^'\\]|\\.)*$/, 'string.invalid'],
          [/'/, 'string', '@string_single'],
          [/[a-zA-Z_][a-zA-Z0-9_]*/, {
            cases: {
              '@keywords': 'keyword',
              '@builtins': 'predefined',
              '@default': 'identifier'
            }
          }],
          [/[+\-*\/%]/, 'operator.arithmetic'],
          [/[=!<>]=?/, 'operator.comparison'],
          [/[&|^~]/, 'operator.bitwise'],
          [/[(){}[\]]/, 'delimiter.bracket'],
          [/[,;:.]/, 'delimiter'],
          [/=/, 'operator.assignment'],
          [/[ \t\r\n]+/, 'white'],
        ],
        comment: [
          [/[^\/*]+/, 'comment'],
          [/\*\//, 'comment', '@pop'],
          [/[\/*]/, 'comment']
        ],
        string: [
          [/[^\\"]+/, 'string'],
          [/\\./, 'string.escape'],
          [/"/, 'string', '@pop']
        ],
        string_single: [
          [/[^\\']+/, 'string'],
          [/\\./, 'string.escape'],
          [/'/, 'string', '@pop']
        ]
      }
    });

    monaco.languages.registerCompletionItemProvider('lynx', {
      provideCompletionItems: (model, position) => {
        const word = model.getWordUntilPosition(position);
        const range = {
          startLineNumber: position.lineNumber,
          endLineNumber: position.lineNumber,
          startColumn: word.startColumn,
          endColumn: word.endColumn
        };

        const suggestions = [];

        palabrasReservadas.forEach(keyword => {
          suggestions.push({
            label: keyword,
            kind: monaco.languages.CompletionItemKind.Keyword,
            insertText: keyword,
            range: range,
            documentation: `Palabra reservada: ${keyword}`,
            detail: 'Palabra clave de Lynx'
          });
        });

        suggestions.push(
          {
            label: 'si-completo',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: 'si (${1:condicion}) {\n\t${2:// código}\n} sino {\n\t${3:// código alternativo}\n}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range: range,
            documentation: 'Estructura condicional completa con si-sino',
            detail: 'Estructura de control'
          },
          {
            label: 'mientras',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: 'mientras (${1:condicion}) {\n\t${2:// código}\n}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range: range,
            documentation: 'Bucle mientras',
            detail: 'Estructura de control'
          },
          {
            label: 'para',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: 'para (val ${1:i} = ${2:0}; ${3:i < 10}; ${4:i = i + 1}) {\n\t${5:// código}\n}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range: range,
            documentation: 'Bucle para con inicialización, condición e incremento',
            detail: 'Estructura de control'
          },
          {
            label: 'fun',
            kind: monaco.languages.CompletionItemKind.Snippet,
            insertText: 'fun ${1:nombre}(${2:parametros}) {\n\t${3:// código}\n\tretornar ${4:valor}\n}',
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range: range,
            documentation: 'Declaración de función con parámetros y retorno',
            detail: 'Función'
          }
        );

        variablesDeclaradas.forEach(variable => {
          suggestions.push({
            label: variable,
            kind: monaco.languages.CompletionItemKind.Variable,
            insertText: variable,
            range: range,
            documentation: `Variable declarada: ${variable}`,
            detail: 'Variable local'
          });
        });

        funcionesDeclaradas.forEach(funcion => {
          suggestions.push({
            label: funcion,
            kind: monaco.languages.CompletionItemKind.Function,
            insertText: `${funcion}($1)`,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range: range,
            documentation: `Función definida: ${funcion}`,
            detail: 'Función personalizada'
          });
        });

        funcionesBuiltIn.forEach(funcion => {
          let insertText = `${funcion}($1)`;
          let documentation = `Función integrada: ${funcion}`;

          switch (funcion) {
            case 'imprimir':
              documentation = 'Imprime valores en la consola';
              insertText = 'imprimir(${1:valor})';
              break;
            case 'longitud':
              documentation = 'Obtiene la longitud de un arreglo o cadena';
              insertText = 'longitud(${1:variable})';
              break;
            case 'tipo':
              documentation = 'Obtiene el tipo de una variable';
              insertText = 'tipo(${1:variable})';
              break;
          }

          suggestions.push({
            label: funcion,
            kind: monaco.languages.CompletionItemKind.Function,
            insertText: insertText,
            insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
            range: range,
            documentation: documentation,
            detail: 'Función integrada'
          });
        });

        return { suggestions };
      }
    });

    monaco.languages.registerHoverProvider('lynx', {
      provideHover: (model, position) => {
        const word = model.getWordAtPosition(position);
        if (!word) return null;

        const wordValue = word.word;
        let contents = [];

        if (palabrasReservadas.includes(wordValue)) {
          contents.push({ value: `**${wordValue}** - Palabra reservada de Lynx` });
        } else if (funcionesBuiltIn.includes(wordValue)) {
          contents.push({ value: `**${wordValue}()** - Función integrada` });
        } else if (variablesDeclaradas.has(wordValue)) {
          contents.push({ value: `**${wordValue}** - Variable declarada` });
        } else if (funcionesDeclaradas.has(wordValue)) {
          contents.push({ value: `**${wordValue}()** - Función definida por el usuario` });
        }

        return contents.length > 0 ? { contents } : null;
      }
    });

    monaco.editor.defineTheme('lynx-theme-advanced', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: '#569CD6', fontStyle: 'bold' },
        { token: 'predefined', foreground: '#DCDCAA', fontStyle: 'bold' },
        { token: 'string', foreground: '#CE9178' },
        { token: 'string.escape', foreground: '#D7BA7D' },
        { token: 'string.invalid', foreground: '#FF6B6B', fontStyle: 'italic' },
        { token: 'number', foreground: '#B5CEA8' },
        { token: 'number.float', foreground: '#B5CEA8' },
        { token: 'number.hex', foreground: '#B5CEA8' },
        { token: 'comment', foreground: '#6A9955', fontStyle: 'italic' },
        { token: 'identifier', foreground: '#9CDCFE' },
        { token: 'operator.arithmetic', foreground: '#D4D4D4' },
        { token: 'operator.comparison', foreground: '#D4D4D4' },
        { token: 'operator.assignment', foreground: '#D4D4D4' },
        { token: 'operator.bitwise', foreground: '#D4D4D4' },
        { token: 'delimiter.bracket', foreground: '#FFD700' },
        { token: 'delimiter', foreground: '#D4D4D4' },
        { token: 'invalid', foreground: '#FF6B6B', fontStyle: 'italic' },
      ],
      colors: {
        'editor.background': '#1E1E1E',
        'editor.foreground': '#D4D4D4',
        'editorLineNumber.foreground': '#858585',
        'editorCursor.foreground': '#AEAFAD',
        'editor.selectionBackground': '#264F78',
        'editor.inactiveSelectionBackground': '#3A3D41',
        'editorIndentGuide.background': '#404040',
        'editorIndentGuide.activeBackground': '#707070',
        'editor.wordHighlightBackground': '#575757B8',
        'editor.wordHighlightStrongBackground': '#004972B8',
      }
    });
  }, [variablesDeclaradas, funcionesDeclaradas]);

  const validarCodigoTiempoReal = useCallback(async (codigoTexto) => {
    if (!codigoTexto.trim() || estadoConexion !== 'conectado') return;

    try {
      const response = await fetch('http://localhost:8000/analizar-lexico', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ codigo: codigoTexto }),
      });

      if (response.ok) {
        const data = await response.json();

        extraerSimbolos(codigoTexto);

        if (editorRef.current && monacoRef.current) {
          const markers = [];

          data.errores.forEach((error, index) => {
            markers.push({
              severity: monacoRef.current.MarkerSeverity.Error,
              startLineNumber: 1,
              startColumn: 1,
              endLineNumber: 1,
              endColumn: 100,
              message: error,
              source: 'lynx-lexer'
            });
          });

          const lineas = codigoTexto.split('\n');
          const warningsEncontrados = [];

          lineas.forEach((linea, indiceLinea) => {
            const declaracionVar = linea.match(/val\s+([a-zA-Z_][a-zA-Z0-9_]*)/);
            if (declaracionVar) {
              const nombreVar = declaracionVar[1];
              const usoVar = new RegExp(`\\b${nombreVar}\\b`, 'g');
              const usosEnCodigo = (codigoTexto.match(usoVar) || []).length;

              if (usosEnCodigo <= 1) {
                warningsEncontrados.push(`Variable '${nombreVar}' declarada pero no utilizada`);
                markers.push({
                  severity: monacoRef.current.MarkerSeverity.Warning,
                  startLineNumber: indiceLinea + 1,
                  startColumn: 1,
                  endLineNumber: indiceLinea + 1,
                  endColumn: linea.length + 1,
                  message: `Variable '${nombreVar}' declarada pero no utilizada`,
                  source: 'lynx-analyzer'
                });
              }
            }
          });

          setWarnings(warningsEncontrados);

          monacoRef.current.editor.setModelMarkers(
            editorRef.current.getModel(),
            'lynx',
            markers
          );
        }
      }
    } catch (error) {
      console.error('Error en validación tiempo real:', error);
    }
  }, [estadoConexion, extraerSimbolos]);

  useEffect(() => {
    if (validacionTiempoReal && codigo.trim()) {
      if (validationTimeoutRef.current) {
        clearTimeout(validationTimeoutRef.current);
      }

      validationTimeoutRef.current = setTimeout(() => {
        validarCodigoTiempoReal(codigo);
      }, 800);
    }

    return () => {
      if (validationTimeoutRef.current) {
        clearTimeout(validationTimeoutRef.current);
      }
    };
  }, [codigo, validacionTiempoReal, validarCodigoTiempoReal]);

  const analizar = async (tipo = 'completo') => {
    if (!codigo.trim()) {
      alert('Por favor, ingresa código para analizar');
      return;
    }

    if (estadoConexion !== 'conectado') {
      alert('No hay conexión con el servidor backend');
      return;
    }

    setCargando(true);
    let url;
    switch (tipo) {
      case 'lexico':
        url = 'http://localhost:8000/analizar-lexico';
        break;
      case 'sintactico':
        url = 'http://localhost:8000/analizar-sintactico';
        break;
      case 'semantico':
        url = 'http://localhost:8000/analizar-semantico';
        break;
      default:
        url = 'http://localhost:8000/analizar';
    }

    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ codigo }),
      });

      if (!response.ok) {
        throw new Error(`Error HTTP: ${response.status}`);
      }

      const data = await response.json();

      setTokens(data.tokens || []);
      setErrores(data.errores || []);
      setAst(data.ast || null);

    } catch (error) {
      console.error('Error:', error);
      alert(`Error al comunicarse con el backend: ${error.message}`);
      setErrores([`Error de conexión: ${error.message}`]);
    } finally {
      setCargando(false);
    }
  };

  const limpiar = () => {
    setCodigo('');
    setTokens([]);
    setErrores([]);
    setWarnings([]);
    setAst(null);
    setResultado('');
    setVariablesDeclaradas(new Set());
    setFuncionesDeclaradas(new Set());

    if (editorRef.current && monacoRef.current) {
      monacoRef.current.editor.setModelMarkers(
        editorRef.current.getModel(),
        'lynx',
        []
      );
    }
  };

  const copiarCodigo = () => {
    navigator.clipboard.writeText(codigo);
    alert('Código copiado al portapapeles');
  };

  const descargarCodigo = () => {
    const blob = new Blob([codigo], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'codigo-lynx.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  const cargarArchivo = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setCodigo(e.target.result);
      };
      reader.readAsText(file);
    }
  };

  const renderASTDiagram = (node, nivel = 0) => {
    if (!node) return null;

    const indent = nivel * 20;
    const nodeId = `node-${Math.random().toString(36).substr(2, 9)}`;

    if (node.tipo_primitivo && node.valor !== undefined) {
      const colorClass = {
        'str': 'bg-green-100 border-green-300 text-green-800',
        'int': 'bg-blue-100 border-blue-300 text-blue-800',
        'float': 'bg-blue-100 border-blue-300 text-blue-800',
        'bool': 'bg-purple-100 border-purple-300 text-purple-800',
        'string': 'bg-gray-100 border-gray-300 text-gray-800'
      }[node.tipo_primitivo] || 'bg-gray-100 border-gray-300 text-gray-800';

      return (
        <div key={nodeId} className="flex items-center my-1" style={{ marginLeft: indent }}>
          <div className={`px-2 py-1 rounded border text-xs ${colorClass}`}>
            {typeof node.valor === 'string' ? `"${node.valor}"` : String(node.valor)}
            <span className="ml-1 opacity-60">({node.tipo_primitivo})</span>
          </div>
        </div>
      );
    }

    if (node.tipo === 'lista' && node.elementos) {
      return (
        <div key={nodeId} className="my-2" style={{ marginLeft: indent }}>
          <div className="flex items-center">
            <div className="w-3 h-3 bg-orange-400 rounded-full mr-2"></div>
            <span className="font-semibold text-orange-600">Lista</span>
          </div>
          <div className="ml-4 border-l-2 border-orange-200 pl-2">
            {node.elementos.map((item, index) => (
              <div key={`${nodeId}-${index}`} className="flex items-start">
                <span className="text-xs text-gray-500 mr-2 mt-1">[{index}]</span>
                <div className="flex-1">
                  {renderASTDiagram(item, nivel + 1)}
                </div>
              </div>
            ))}
          </div>
        </div>
      );
    }

    if (typeof node === 'object' && node !== null && node.tipo) {
      const colors = {
        'DeclaracionVariable': 'bg-blue-500',
        'AsignacionVariable': 'bg-green-500',
        'EstructuraSi': 'bg-purple-500',
        'EstructuraMientras': 'bg-red-500',
        'ExpresionBinaria': 'bg-yellow-500',
        'Imprimir': 'bg-pink-500'
      };

      const bgColor = colors[node.tipo] || 'bg-gray-500';

      return (
        <div key={nodeId} className="my-2" style={{ marginLeft: indent }}>
          <div className="flex items-center">
            <div className={`w-3 h-3 ${bgColor} rounded-full mr-2`}></div>
            <span className="font-semibold text-gray-700">{node.tipo}</span>
          </div>
          <div className="ml-4 border-l-2 border-gray-200 pl-2">
            {Object.entries(node).map(([key, value]) => {
              if (key === 'tipo') return null;
              return (
                <div key={`${nodeId}-${key}`} className="my-1">
                  <span className="text-purple-600 font-medium text-sm">{key}:</span>
                  <div className="ml-2">
                    {renderASTDiagram(value, nivel + 1)}
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      );
    }

    return (
      <div key={nodeId} className="inline-block px-2 py-1 bg-gray-100 rounded text-xs text-gray-600">
        {String(node)}
      </div>
    );
  };

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    configurarLynxAvanzado(monaco);
    extraerSimbolos(codigo);
  };

  const getEstadoConexionStyle = () => {
    switch (estadoConexion) {
      case 'conectado':
        return 'bg-green-100 text-green-800 border-green-300';
      case 'desconectado':
        return 'bg-red-100 text-red-800 border-red-300';
      case 'error':
        return 'bg-yellow-100 text-yellow-800 border-yellow-300';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-300';
    }
  };

  const getEstadoConexionTexto = () => {
    switch (estadoConexion) {
      case 'conectado':
        return 'Conectado al servidor';
      case 'desconectado':
        return 'Sin conexión al servidor';
      case 'error':
        return 'Error de conexión';
      default:
        return 'Verificando conexión...';
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <Code className="text-blue-600" />
            Editor Lynx
          </h1>
          <p className="text-gray-600 mb-4">
            Editor con análisis en tiempo real, autocompletado inteligente y validación sintáctica
          </p>
          <div className={`inline-flex items-center gap-2 px-3 py-1 rounded-full text-sm border ${getEstadoConexionStyle()}`}>
            <div className={`w-2 h-2 rounded-full ${estadoConexion === 'conectado' ? 'bg-green-500' : estadoConexion === 'desconectado' ? 'bg-red-500' : 'bg-yellow-500'}`}></div>
            {getEstadoConexionTexto()}
          </div>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          <div className="bg-white rounded-lg shadow-sm">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <FileText size={20} />
                Editor de Código
              </h2>
              <div className="flex items-center gap-4">
                <div className="flex items-center gap-2 text-sm">
                  <Lightbulb size={16} className="text-yellow-500" />
                  <span className="text-gray-600">
                    Variables: {variablesDeclaradas.size} | Funciones: {funcionesDeclaradas.size}
                  </span>
                </div>
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={validacionTiempoReal}
                    onChange={(e) => setValidacionTiempoReal(e.target.checked)}
                    className="rounded"
                  />
                  Análisis en tiempo real
                </label>
                <Settings size={16} className="text-gray-400" />
              </div>
            </div>

            <div className="p-4">
              <div className="flex gap-2 mb-4 flex-wrap">
                <button
                  onClick={copiarCodigo}
                  className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-colors"
                >
                  <Copy size={16} />
                  Copiar
                </button>
                <button
                  onClick={descargarCodigo}
                  className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm transition-colors"
                >
                  <Download size={16} />
                  Descargar
                </button>
                <label className="flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 rounded-lg text-sm cursor-pointer transition-colors">
                  <Upload size={16} />
                  Cargar
                  <input
                    type="file"
                    accept=".txt,.lynx"
                    onChange={cargarArchivo}
                    className="hidden"
                  />
                </label>
                <button
                  onClick={limpiar}
                  className="flex items-center gap-2 px-3 py-2 bg-red-100 hover:bg-red-200 text-red-700 rounded-lg text-sm transition-colors"
                >
                  <RotateCcw size={16} />
                  Limpiar
                </button>
              </div>

              <div className="border rounded-lg overflow-hidden">
                <Editor
                  height="500px"
                  language="lynx"
                  theme="lynx-theme-advanced"
                  value={codigo}
                  onChange={setCodigo}
                  onMount={handleEditorDidMount}
                  options={{
                    minimap: { enabled: true },
                    fontSize: 14,
                    wordWrap: 'on',
                    automaticLayout: true,
                    suggestOnTriggerCharacters: true,
                    quickSuggestions: true,
                    parameterHints: { enabled: true },
                    hover: { enabled: true },
                    folding: true,
                    lineNumbers: 'on',
                    renderLineHighlight: 'all',
                    scrollBeyondLastLine: false,
                    smoothScrolling: true,
                    cursorBlinking: 'smooth',
                    renderWhitespace: 'selection',
                    bracketPairColorization: { enabled: true },
                    guides: {
                      bracketPairs: true,
                      indentation: true
                    }
                  }}
                />
              </div>

              <div className="flex gap-3 mt-4 flex-wrap">
                <button
                  onClick={() => analizar('lexico')}
                  disabled={cargando}
                  className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
                >
                  <Zap size={16} />
                  {cargando ? 'Analizando...' : 'Análisis Léxico'}
                </button>
                <button
                  onClick={() => analizar('sintactico')}
                  disabled={cargando}
                  className="flex items-center gap-2 px-4 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
                >
                  <TreePine size={16} />
                  {cargando ? 'Analizando...' : 'Análisis Sintáctico'}
                </button>
                <button
                  onClick={() => analizar('semantico')}
                  disabled={cargando}
                  className="flex items-center gap-2 px-4 py-2 bg-orange-600 hover:bg-orange-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
                >
                  <Brain size={16} />
                  {cargando ? 'Analizando...' : 'Análisis Semántico'}
                </button>
                <button
                  onClick={() => analizar('completo')}
                  disabled={cargando}
                  className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-700 disabled:bg-gray-400 text-white rounded-lg transition-colors"
                >
                  <Code size={16} />
                  {cargando ? 'Analizando...' : 'Análisis Completo'}
                </button>
              </div>
            </div>
          </div>

          <div className="space-y-6">
            {(errores.length > 0 || warnings.length > 0) && (
              <div className="bg-white rounded-lg shadow-sm">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <AlertCircle className="text-red-500" size={20} />
                    Diagnósticos
                  </h3>
                </div>
                <div className="p-4 space-y-3">
                  {errores.map((error, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-red-50 border border-red-200 rounded-lg">
                      <AlertCircle className="text-red-500 mt-0.5" size={16} />
                      <div>
                        <div className="font-medium text-red-800">Error</div>
                        <div className="text-sm text-red-600">{error}</div>
                      </div>
                    </div>
                  ))}
                  {warnings.map((warning, index) => (
                    <div key={index} className="flex items-start gap-3 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
                      <AlertCircle className="text-yellow-500 mt-0.5" size={16} />
                      <div>
                        <div className="font-medium text-yellow-800">Advertencia</div>
                        <div className="text-sm text-yellow-600">{warning}</div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {tokens.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <Zap className="text-blue-500" size={20} />
                    Tokens Identificados ({tokens.length})
                  </h3>
                </div>
                <div className="p-4">
                  <div className="max-h-60 overflow-y-auto">
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                      {tokens.map((token, index) => {
                        const colorMap = {
                          'PALABRA_RESERVADA': 'bg-blue-100 text-blue-800 border-blue-300',
                          'ID': 'bg-green-100 text-green-800 border-green-300',
                          'NUMERO': 'bg-purple-100 text-purple-800 border-purple-300',
                          'CADENA': 'bg-orange-100 text-orange-800 border-orange-300',
                          'OPERADOR': 'bg-red-100 text-red-800 border-red-300',
                          'ASIGNACION': 'bg-red-100 text-red-800 border-red-300',
                          'DELIMITADOR': 'bg-gray-100 text-gray-800 border-gray-300'
                        };

                        const colorClass = colorMap[token.tipo] || 'bg-gray-100 text-gray-800 border-gray-300';

                        return (
                          <div key={index} className={`px-3 py-2 rounded-lg border text-sm ${colorClass}`}>
                            <div className="font-medium">Lexema: {token.lexema}</div>
                            <div className="text-xs opacity-75">Tipo: {token.tipo}</div>
                            <div className="text-xs opacity-75">Línea: {token.linea}</div>
                            <div className="text-xs opacity-75">Columna: {token.columna}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {ast && (
              <div className="bg-white rounded-lg shadow-sm">
                <div className="p-4 border-b border-gray-200 flex justify-between items-center">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <TreePine className="text-green-500" size={20} />
                    Árbol Sintáctico Abstracto
                  </h3>
                  <button
                    onClick={() => setMostrarAST(!mostrarAST)}
                    className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                  >
                    {mostrarAST ? 'Ocultar' : 'Mostrar'} AST
                  </button>
                </div>
                {mostrarAST && (
                  <div className="p-4">
                    <div className="max-h-96 overflow-y-auto bg-gray-50 p-4 rounded-lg">
                      {renderASTDiagram(ast)}
                    </div>
                  </div>
                )}
              </div>
            )}

            <div className="bg-white rounded-lg shadow-sm">
              <div className="p-4 border-b border-gray-200">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <CheckCircle className="text-green-500" size={20} />
                  Estado del Análisis
                </h3>
              </div>
              <div className="p-4 space-y-3">
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Variables declaradas:</span>
                  <span className="font-medium">{variablesDeclaradas.size}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Funciones declaradas:</span>
                  <span className="font-medium">{funcionesDeclaradas.size}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Líneas de código:</span>
                  <span className="font-medium">{codigo.split('\n').length}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Caracteres:</span>
                  <span className="font-medium">{codigo.length}</span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Errores encontrados:</span>
                  <span className={`font-medium ${errores.length > 0 ? 'text-red-600' : 'text-green-600'}`}>
                    {errores.length}
                  </span>
                </div>
                <div className="flex justify-between items-center text-sm">
                  <span className="text-gray-600">Advertencias:</span>
                  <span className={`font-medium ${warnings.length > 0 ? 'text-yellow-600' : 'text-green-600'}`}>
                    {warnings.length}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 text-center text-gray-500 text-sm">
          <p>Editor Lynx v2.0 - Desarrollado con React y Monaco Editor</p>
          <p>Soporte para análisis léxico, sintáctico, semántico y ejecución de código</p>
        </div>
      </div>
    </div>
  );
}
