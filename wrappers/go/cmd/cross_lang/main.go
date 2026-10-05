// Command cross_lang is the Go conformance runner.
//
// It reads tests/cross_language_queries.json, answers each query through the
// Go wrapper, and prints key-sorted JSON (2-space indent) that must be
// byte-identical to the Python, JavaScript and Rust runners. It is diffed by
// tools/check_cross_language.sh. encoding/json sorts map keys.
package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"

	ec "github.com/slimissa/exchange-calendar/wrappers/go"
)

type query struct {
	Op    string            `json:"op"`
	Args  []json.RawMessage `json:"args"`
	Label string            `json:"label"`
}

func str(raw json.RawMessage) string {
	var s string
	if err := json.Unmarshal(raw, &s); err != nil {
		die("bad string arg: %v", err)
	}
	return s
}

func die(format string, a ...any) {
	fmt.Fprintf(os.Stderr, format+"\n", a...)
	os.Exit(2)
}

// nullable maps the wrapper's empty-string "absent" to JSON null.
func nullable(s string) any {
	if s == "" {
		return nil
	}
	return s
}

func confidenceJSON(c ec.ConfidenceEntry) map[string]any {
	m := map[string]any{
		"source":        c.Source,
		"last_verified": nullable(c.LastVerified),
		"level":         c.Level,
	}
	if c.Note != "" {
		m["note"] = c.Note
	}
	return m
}

func main() {
	_, self, _, _ := runtime.Caller(0)
	root := filepath.Join(filepath.Dir(self), "..", "..", "..", "..")
	if wd, err := os.Getwd(); err == nil {
		// `go run ./cmd/cross_lang` from wrappers/go: prefer the repo root
		// relative to the working directory when the source path is unavailable.
		if _, err := os.Stat(filepath.Join(root, "calendar.json")); err != nil {
			root = filepath.Join(wd, "..", "..")
		}
	}

	raw, err := os.ReadFile(filepath.Join(root, "tests", "cross_language_queries.json"))
	if err != nil {
		die("read fixture: %v", err)
	}
	var fixture struct {
		Queries []query `json:"queries"`
	}
	if err := json.Unmarshal(raw, &fixture); err != nil {
		die("parse fixture: %v", err)
	}

	r, err := ec.LoadRegistry(filepath.Join(root, "calendar.json"))
	if err != nil {
		die("load calendar.json: %v", err)
	}

	out := map[string]any{}
	for _, q := range fixture.Queries {
		var v any
		switch q.Op {
		case "sessions":
			list := []map[string]any{}
			for _, s := range r.Sessions(str(q.Args[0])) {
				list = append(list, map[string]any{
					"type":  s.Type,
					"open":  nullable(s.Open),
					"close": nullable(s.Close),
					"at":    nullable(s.At),
				})
			}
			v = list
		case "confidence":
			var year int
			if err := json.Unmarshal(q.Args[1], &year); err != nil {
				die("bad year: %v", err)
			}
			if c, ok := r.Confidence(str(q.Args[0]), year); ok {
				v = confidenceJSON(c)
			}
		case "is_open":
			v = r.IsOpen(str(q.Args[0]), str(q.Args[1]), str(q.Args[2]))
		case "as_of":
			conf := map[string]any{}
			var asOf any
			if rec, ok := r.AsOf(str(q.Args[0]), str(q.Args[1])); ok {
				for y, c := range rec["confidence"].(map[string]ec.ConfidenceEntry) {
					conf[y] = confidenceJSON(c)
				}
				asOf = rec["_as_of"]
			}
			v = map[string]any{"confidence": conf, "_as_of": asOf}
		default:
			die("unknown op %s", q.Op)
		}
		out[q.Label] = v
	}

	var buf bytes.Buffer
	enc := json.NewEncoder(&buf)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", "  ")
	if err := enc.Encode(out); err != nil {
		die("encode: %v", err)
	}
	os.Stdout.Write(buf.Bytes())
}
