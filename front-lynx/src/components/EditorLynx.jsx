import { useState } from 'react';
import { Editor } from '@monaco-editor/react';
import axios from 'axios';

export default function EditorLynx() {
  const [codigo, setCodigo] = useState('');
  const [tokens, setTokens] = useState([]);
  const [errores, setErrores] = useState([]);

  const analizar = async () => {
    const url = 'http://localhost:8000/analizar';
    try {
      const res = await axios.post(url, { codigo });
      setTokens(res.data.tokens);
      setErrores(res.data.errores);

      if (res.data.errores.length === 0) {
        alert('Compilación Correcta');
      } else {
        alert('Errores Encontrados, Compilación Fallida');
      }
    } catch (err) {
      alert('Error al comunicarse con el backend');
    }
  };

  const handleEditorWillMount = (monaco) => {
    const palabrasReservadas = [
      "y", "salir", "hacer", "sino", "sinosi", "falso", "para", "fun", "si", "en",
      "val", "nulo", "no", "o", "repetir", "retornar", "entonces", "verdadero",
      "hasta", "mientras", "intentar", "capturar", "segun", "caso", "finalmente",
      "parar", "predeterminado"
    ];

    const regexPalabras = `\\b(${palabrasReservadas.join("|")})\\b`;

    monaco.languages.register({ id: 'lynx' });

    monaco.languages.setMonarchTokensProvider('lynx', {
      tokenizer: {
        root: [
          [new RegExp(regexPalabras), "keyword"],
          [/[a-zA-Z_][a-zA-Z0-9_]*/, "identifier"],
          [/"([a-zA-Z0-9@\'#$%^/=_\-\}\{\.\,\<\>\?\`\~\)\(\*\!\+\ \[\]])*\"|\'([a-zA-Z0-9@\'#$%^/=_\-\}\{\.\,\<\>\?\`\~\)\(\*\!\+\ \[\]])*\'/, "string"],
          [/\b\d+\.\d*|\.\d+|\b\d+\b/, "number"],
          [/\/\/.*/, "comment"],
          [/\/\*/, "comment", "@comment"],
        ],
        comment: [
          [/[^\/*]+/, "comment"],
          [/\/\*/, "comment", "@push"], // permite comentarios anidados
          [/\*\//, "comment", "@pop"],
          [/[\/*]/, "comment"]
        ]
      }
    });

    monaco.languages.setLanguageConfiguration('lynx', {
      comments: {
        lineComment: '//',
      },
      brackets: [
        ['{', '}'],
        ['[', ']'],
        ['(', ')'],
      ],
      autoClosingPairs: [
        { open: '{', close: '}' },
        { open: '[', close: ']' },
        { open: '(', close: ')' },
        { open: '"', close: '"', notIn: ['string'] },
      ],
    });

    monaco.languages.registerCompletionItemProvider('lynx', {
      provideCompletionItems: () => {
        const suggestions = palabrasReservadas.map((word) => ({
          label: word,
          kind: monaco.languages.CompletionItemKind.Keyword,
          insertText: word,
        }));

        return { suggestions };
      },
    });
  };


  return (
    <div className="p-4">
      <Editor
        height="40vh"
        defaultLanguage="lynx"
        defaultValue=""
        value={codigo}
        onChange={(val) => setCodigo(val || '')}
        onMount={(_, monaco) => handleEditorWillMount(monaco)}
        theme="vs-dark"
      />

      <button onClick={analizar} className="bg-blue-600 text-white px-4 py-2 my-4 rounded">
        Analizar Código
      </button>

      <h2 className="text-xl font-bold mb-2">Tokens:</h2>
      <table className="w-full border mb-4">
        <thead>
          <tr>
            <th>Lexema</th>
            <th>Tipo</th>
            <th>Línea</th>
            <th>Columna</th>
          </tr>
        </thead>
        <tbody>
          {tokens.map((t, i) => (
            <tr key={i}>
              <td>{t.lexema}</td>
              <td>{t.tipo}</td>
              <td>{t.linea}</td>
              <td>{t.columna}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <h2 className="text-xl font-bold mb-2">Errores:</h2>
      <table className="w-full border">
        <thead>
          <tr>
            <th>Mensaje</th>
          </tr>
        </thead>
        <tbody>
          {errores.map((e, i) => (
            <tr key={i}>
              <td>{e}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

