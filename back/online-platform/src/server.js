import express from "express";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const app = express();
// Sirve el build estático de la app React (client/) sin ninguna lógica de negocio.
app.use(express.static(path.join(__dirname, "../public")));

const port = process.env.PORT || 3000;
// Arranca el servidor de archivos estáticos.
app.listen(port, () => console.log(`online-platform (estático) escuchando en :${port}`));
