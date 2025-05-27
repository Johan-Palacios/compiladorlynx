import { useState, useRef, useEffect } from 'react';
import { Editor } from '@monaco-editor/react';
import { AlertCircle, CheckCircle, Code, Play, FileText, Zap, TreePine, Settings } from 'lucide-react';

export default function LynxEditorAvanzado() {
  const [codigo, setCodigo] = useState(`// Ejemplo completo de Lynx
val mensaje = "Bienvenido a Lynx"
imprimir(mensaje)

// Variables y operaciones
val x = 10
val y = 20
val suma = x + y

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
  const [ast, setAst] = useState(null);
  const [cargando, setCargando] = useState(false);
  const [validacionTiempoReal, setValidacionTiempoReal] = useState(true);
  const editorRef = useRef(null);
  const monacoRef = useRef(null);

  // Configuración del lenguaje Lynx para Monaco
  useEffect(() => {
    const configurarLynx = (monaco) => {
      // Registrar el lenguaje Lynx
      monaco.languages.register({ id: 'lynx' });

      // Definir tokens y sintaxis
      monaco.languages.setMonarchTokensProvider('lynx', {
        tokenizer: {
          root: [
            // Palabras reservadas
            [/\b(val|si|sino|sinosi|mientras|para|fun|retornar|imprimir|verdadero|falso|nulo|y|o|no|hacer|salir|en|repetir|hasta|intentar|capturar|segun|caso|predeterminado|finalmente|parar)\b/, 'keyword'],
            
            // Identificadores
            [/[a-zA-Z_][a-zA-Z0-9_]*/, 'identifier'],
            
            // Números
            [/\d+\.\d+/, 'number.float'],
            [/\d+/, 'number'],
            
            // Cadenas
            [/"([^"\\]|\\.)*"/, 'string'],
            [/'([^'\\]|\\.)*'/, 'string'],
            
            // Comentarios
            [/\/\/.*$/, 'comment'],
            [/\/\*/, 'comment', '@comment'],
            
            // Operadores
            [/[+\-*\/%]/, 'operator'],
            [/[=!<>]=?/, 'operator'],
            [/[(){}[\]]/, 'bracket'],
            [/[,;:]/, 'delimiter'],
          ],
          comment: [
            [/[^/*]+/, 'comment'],
            [/\*\//, 'comment', '@pop'],
            [/[/*]/, 'comment']
          ]
        }
      });

      // Configurar autocompletado
      monaco.languages.registerCompletionItemProvider('lynx', {
        provideCompletionItems: (model, position) => {
          const suggestions = [
            // Palabras clave
            {
              label: 'val',
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: 'val ${1:nombre} = ${2:valor}',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Declaración de variable'
            },
            {
              label: 'si',
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: 'si (${1:condicion}) {\n\t${2:// código}\n}',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Estructura condicional'
            },
            {
              label: 'mientras',
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: 'mientras (${1:condicion}) {\n\t${2:// código}\n}',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Bucle mientras'
            },
            {
              label: 'para',
              kind: monaco.languages.CompletionItemKind.Keyword,
              insertText: 'para (val ${1:i} = ${2:0}; ${3:i < 10}; ${4:i = i + 1}) {\n\t${5:// código}\n}',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Bucle para'
            },
            {
              label: 'fun',
              kind: monaco.languages.CompletionItemKind.Function,
              insertText: 'fun ${1:nombre}(${2:parametros}) {\n\t${3:// código}\n\tretornar ${4:valor}\n}',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Declaración de función'
            },
            {
              label: 'imprimir',
              kind: monaco.languages.CompletionItemKind.Function,
              insertText: 'imprimir(${1:mensaje})',
              insertTextRules: monaco.languages.CompletionItemInsertTextRule.InsertAsSnippet,
              documentation: 'Función para imprimir en consola'
            }
          ];

          return { suggestions };
        }
      });

      // Configurar tema personalizado
      monaco.editor.defineTheme('lynx-theme', {
        base: 'vs-dark',
        inherit: true,
        rules: [
          { token: 'keyword', foreground: '#569CD6', fontStyle: 'bold' },
          { token: 'string', foreground: '#CE9178' },
          { token: 'number', foreground: '#B5CEA8' },
          { token: 'number.float', foreground: '#B5CEA8' },
          { token: 'comment', foreground: '#6A9955', fontStyle: 'italic' },
          { token: 'identifier', foreground: '#9CDCFE' },
          { token: 'operator', foreground: '#D4D4D4' },
          { token: 'bracket', foreground: '#FFD700' },
        ],
        colors: {
          'editor.background': '#1E1E1E',
          'editor.foreground': '#D4D4D4',
          'editorLineNumber.foreground': '#858585',
          'editorCursor.foreground': '#AEAFAD',
        }
      });
    };

    // La configuración se aplicará cuando Monaco esté disponible
    if (monacoRef.current) {
      configurarLynx(monacoRef.current);
    }
  }, []);

  // Validación en tiempo real
  useEffect(() => {
    if (validacionTiempoReal && codigo.trim()) {
      const timer = setTimeout(() => {
        validarCodigo();
      }, 1000); // Validar después de 1 segundo de inactividad

      return () => clearTimeout(timer);
    }
  }, [codigo, validacionTiempoReal]);

  const validarCodigo = async () => {
    if (!codigo.trim()) return;

    try {
      const response = await fetch('http://localhost:8000/analizar-lexico', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ codigo }),
      });

      if (response.ok) {
        const data = await response.json();
        
        // Marcar errores en el editor
        if (editorRef.current && monacoRef.current) {
          const markers = data.errores.map((error, index) => ({
            severity: monacoRef.current.MarkerSeverity.Error,
            startLineNumber: 1,
            startColumn: 1,
            endLineNumber: 1,
            endColumn: 100,
            message: error,
            source: 'lynx'
          }));

          monacoRef.current.editor.setModelMarkers(
            editorRef.current.getModel(),
            'lynx',
            markers
          );
        }
      }
    } catch (error) {
      console.error('Error en validación:', error);
    }
  };

  const analizar = async (tipo = 'completo') => {
    if (!codigo.trim()) {
      alert('Por favor, ingresa código para analizar');
      return;
    }

    setCargando(true);
    
    let url = 'http://localhost:8000/analizar';
    if (tipo === 'lexico') {
      url = 'http://localhost:8000/analizar-lexico';
    } else if (tipo === 'sintactico') {
      url = 'http://localhost:8000/analizar-sintactico';
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
    setAst(null);
    
    // Limpiar marcadores del editor
    if (editorRef.current && monacoRef.current) {
      monacoRef.current.editor.setModelMarkers(
        editorRef.current.getModel(),
        'lynx',
        []
      );
    }
  };

  const renderASTDiagram = (node, nivel = 0) => {
    if (!node) return null;
    
    const indent = nivel * 20;
    const nodeId = `node-${Math.random().toString(36).substr(2, 9)}`;
    
    // Valor primitivo
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
    
    // Lista
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
    
    // Nodo AST
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
    
    // Aplicar configuración del lenguaje
    monaco.languages.register({ id: 'lynx' });
    
    // Configurar tokens y sintaxis (repetir aquí para asegurar que se aplique)
    monaco.languages.setMonarchTokensProvider('lynx', {
      tokenizer: {
        root: [
          [/\b(val|si|sino|sinosi|mientras|para|fun|retornar|imprimir|verdadero|falso|nulo|y|o|no|hacer|salir|en|repetir|hasta|intentar|capturar|segun|caso|predeterminado|finalmente|parar)\b/, 'keyword'],
          [/[a-zA-Z_][a-zA-Z0-9_]*/, 'identifier'],
          [/\d+\.\d+/, 'number.float'],
          [/\d+/, 'number'],
          [/"([^"\\]|\\.)*"/, 'string'],
          [/'([^'\\]|\\.)*'/, 'string'],
          [/\/\/.*$/, 'comment'],
          [/\/\*/, 'comment', '@comment'],
          [/[+\-*\/%]/, 'operator'],
          [/[=!<>]=?/, 'operator'],
          [/[(){}[\]]/, 'bracket'],
          [/[,;:]/, 'delimiter'],
        ],
        comment: [
          [/[^/*]+/, 'comment'],
          [/\*\//, 'comment', '@pop'],
          [/[/*]/, 'comment']
        ]
      }
    });

    // Aplicar tema
    monaco.editor.defineTheme('lynx-theme', {
      base: 'vs-dark',
      inherit: true,
      rules: [
        { token: 'keyword', foreground: '#569CD6', fontStyle: 'bold' },
        { token: 'string', foreground: '#CE9178' },
        { token: 'number', foreground: '#B5CEA8' },
        { token: 'number.float', foreground: '#B5CEA8' },
        { token: 'comment', foreground: '#6A9955', fontStyle: 'italic' },
        { token: 'identifier', foreground: '#9CDCFE' },
        { token: 'operator', foreground: '#D4D4D4' },
        { token: 'bracket', foreground: '#FFD700' },
      ],
      colors: {
        'editor.background': '#1E1E1E',
        'editor.foreground': '#D4D4D4',
      }
    });
  };

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <h1 className="text-3xl font-bold text-gray-900 mb-2 flex items-center gap-3">
            <Code className="text-blue-600" />
            Editor Lynx Avanzado
          </h1>
          <p className="text-gray-600">
            Editor con autocompletado, validación en tiempo real y visualización de AST
          </p>
        </div>

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-6">
          {/* Editor */}
          <div className="bg-white rounded-lg shadow-sm">
            <div className="p-4 border-b border-gray-200 flex justify-between items-center">
              <h2 className="text-xl font-semibold text-gray-900 flex items-center gap-2">
                <FileText size={20} />
                Editor de Código
              </h2>
              <div className="flex items-center gap-2">
                <label className="flex items-center gap-2 text-sm">
                  <input
                    type="checkbox"
                    checked={validacionTiempoReal}
                    onChange={(e) => setValidacionTiempoReal(e.target.checked)}
                    className="rounded"
                  />
                  Validación en tiempo real
                </label>
                <Settings size={16} className="text-gray-400" />
              </div>
            </div>
            <div className="p-4">
              <div className="border rounded-lg overflow-hidden" style={{ height: '500px' }}>
                <Editor
                  height="100%"
                  language="lynx"
                  theme="lynx-theme"
                  value={codigo}
                  onChange={(value) => setCodigo(value || '')}
                  onMount={handleEditorDidMount}
                  options={{
                    minimap: { enabled: false },
                    fontSize: 14,
                    lineNumbers: 'on',
                    roundedSelection: false,
                    scrollBeyondLastLine: false,
                    automaticLayout: true,
                    tabSize: 2,
                    insertSpaces: true,
                    wordWrap: 'on',
                    suggest: {
                      showKeywords: true,
                      showSnippets: true,
                    }
                  }}
                />
              </div>
              
              <div className="flex flex-wrap gap-2 mt-4">
                <button
                  onClick={() => analizar('completo')}
                  disabled={cargando}
                  className="bg-blue-600 hover:bg-blue-700 disabled:bg-blue-400 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <Play size={16} />
                  {cargando ? 'Analizando...' : 'Análisis Completo'}
                </button>
                
                <button
                  onClick={() => analizar('lexico')}
                  disabled={cargando}
                  className="bg-green-600 hover:bg-green-700 disabled:bg-green-400 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <Zap size={16} />
                  Solo Léxico
                </button>
                
                <button
                  onClick={() => analizar('sintactico')}
                  disabled={cargando}
                  className="bg-purple-600 hover:bg-purple-700 disabled:bg-purple-400 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
                >
                  <Code size={16} />
                  Solo Sintáctico
                </button>
                
                <button
                  onClick={limpiar}
                  className="bg-red-600 hover:bg-red-700 text-white px-4 py-2 rounded-lg transition-colors"
                >
                  Limpiar
                </button>
              </div>
            </div>
          </div>

          {/* Resultados */}
          <div className="space-y-6">
            {/* Estado */}
            {(tokens.length > 0 || errores.length > 0) && (
              <div className="bg-white rounded-lg shadow-sm p-4">
                <div className="flex items-center gap-2 mb-2">
                  {errores.length === 0 ? (
                    <>
                      <CheckCircle className="text-green-500" size={20} />
                      <span className="text-green-700 font-semibold">Análisis Exitoso</span>
                    </>
                  ) : (
                    <>
                      <AlertCircle className="text-red-500" size={20} />
                      <span className="text-red-700 font-semibold">Errores Encontrados</span>
                    </>
                  )}
                </div>
                <p className="text-sm text-gray-600">
                  {tokens.length} tokens encontrados, {errores.length} errores
                </p>
              </div>
            )}

            {/* Errores */}
            {errores.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-red-700 flex items-center gap-2">
                    <AlertCircle size={18} />
                    Errores ({errores.length})
                  </h3>
                </div>
                <div className="p-4">
                  <div className="space-y-2">
                    {errores.map((error, index) => (
                      <div key={index} className="bg-red-50 border border-red-200 rounded-lg p-3">
                        <p className="text-red-800 text-sm font-mono">{error}</p>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Tokens */}
            {tokens.length > 0 && (
              <div className="bg-white rounded-lg shadow-sm">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900">
                    Tokens ({tokens.length})
                  </h3>
                </div>
                <div className="overflow-auto max-h-64">
                  <table className="w-full text-sm">
                    <thead className="bg-gray-50 sticky top-0">
                      <tr>
                        <th className="text-left p-3 font-semibold">Lexema</th>
                        <th className="text-left p-3 font-semibold">Tipo</th>
                        <th className="text-left p-3 font-semibold">Línea</th>
                        <th className="text-left p-3 font-semibold">Columna</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tokens.map((token, index) => (
                        <tr key={index} className="border-t border-gray-200 hover:bg-gray-50">
                          <td className="p-3 font-mono text-blue-600">{token.lexema}</td>
                          <td className="p-3 text-green-600">{token.tipo}</td>
                          <td className="p-3">{token.linea}</td>
                          <td className="p-3">{token.columna}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            )}

            {/* AST Diagram */}
            {ast && (
              <div className="bg-white rounded-lg shadow-sm">
                <div className="p-4 border-b border-gray-200">
                  <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                    <TreePine size={18} />
                    Árbol de Sintaxis Abstracta (AST)
                  </h3>
                </div>
                <div className="p-4 overflow-auto max-h-96">
                  <div className="text-sm">
                    {renderASTDiagram(ast)}
                  </div>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
