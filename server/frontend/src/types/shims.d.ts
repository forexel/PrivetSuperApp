// Generic shims so TS accepts asset imports during type-check
declare module '*.css' {
  const content: string
  export default content
}

declare module '*.svg' {
  const src: string
  export default src
}

