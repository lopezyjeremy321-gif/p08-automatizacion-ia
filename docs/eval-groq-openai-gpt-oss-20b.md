# Evaluacion P08 - groq:openai/gpt-oss-20b

- Casos: 50 (15 ventas, 15 soporte, 10 spam, 10 dificiles). Etiquetas escritas a mano ANTES de ejecutar el modelo.
- Aciertos exactos: **48/50 = 96.0 %** (1 repeticion).
- Margen: IC 95 % Wilson 86.5 % a 98.9 % (aprox. +-6 pts). Con 50 casos y 1 rep, diferencias menores a ese margen no son concluyentes.
- Cobertura (no 'incierto'): 98.0 %; exactitud entre los respondidos: 98.0 %.
- **Falso positivo de spam** (correo legitimo marcado como spam): 0/37 = 0.0 % 
- Latencia media por clasificacion: 0.86 s

## Matriz de confusion (filas = etiqueta humana, columnas = prediccion)

| real \ pred | ventas | soporte | spam | incierto |
|---|---|---|---|---|
| **ventas** | 18 | 0 | 0 | 0 |
| **soporte** | 0 | 19 | 0 | 0 |
| **spam** | 1 | 0 | 11 | 1 |

## Precision y recall

| clase | n real | precision | recall |
|---|---|---|---|
| ventas | 18 | 94.7 % | 100.0 % |
| soporte | 19 | 100.0 % | 100.0 % |
| spam | 13 | 100.0 % | 84.6 % |

## Por grupo

| grupo | aciertos |
|---|---|
| ventas | 15/15 |
| soporte | 15/15 |
| spam | 9/10 |
| dificil | 9/10 |

## Borradores (ventas/soporte predichos): 38 generados; aceptados del LLM sin tocar: 36; plantilla segura por rechazo de validador: 2

## Tabla de aciertos por caso

| id | grupo | real | pred | conf | ok | razon | lat s | asunto |
|---|---|---|---|---|---|---|---|---|
| v01 | ventas | ventas | ventas | 0.95 | si | ok | 5.26 | Cotizacion para mi oficina |
| v02 | ventas | ventas | ventas | 0.95 | si | ok | 0.59 | Demo del servicio |
| v03 | ventas | ventas | ventas | 0.95 | si | ok | 0.56 | Precio mayorista |
| v04 | ventas | ventas | ventas | 0.95 | si | ok | 0.69 | Cuanto cuesta el plan anual |
| v05 | ventas | ventas | ventas | 0.95 | si | ok | 0.55 | Propuesta para restaurante |
| v06 | ventas | ventas | ventas | 0.95 | si | ok | 0.39 | Quiero adquirir licencias |
| v07 | ventas | ventas | ventas | 0.95 | si | ok | 0.65 | Informacion de planes |
| v08 | ventas | ventas | ventas | 0.95 | si | ok | 0.75 | Consulta comercial |
| v09 | ventas | ventas | ventas | 0.95 | si | ok | 2.13 | Plan para freelancers |
| v10 | ventas | ventas | ventas | 0.95 | si | ok | 0.92 | Presupuesto de implementacion |
| v11 | ventas | ventas | ventas | 0.95 | si | ok | 0.5 | Me interesa su producto |
| v12 | ventas | ventas | ventas | 0.95 | si | ok | 1.18 | Cotizar renovacion con mas usuarios |
| v13 | ventas | ventas | ventas | 0.95 | si | ok | 1.28 | Alianza y precios para revendedores |
| v14 | ventas | ventas | ventas | 0.95 | si | ok | 1.53 | Pregunta antes de comprar |
| v15 | ventas | ventas | ventas | 0.95 | si | ok | 0.51 | Solicitud de demo y tarifas |
| s01 | soporte | soporte | soporte | 0.95 | si | ok | 1.1 | No puedo entrar a mi cuenta |
| s02 | soporte | soporte | soporte | 0.95 | si | ok | 1.58 | Error al exportar reportes |
| s03 | soporte | soporte | soporte | 0.95 | si | ok | 0.94 | Cobro duplicado |
| s04 | soporte | soporte | soporte | 0.95 | si | ok | 0.63 | La aplicacion se cierra sola |
| s05 | soporte | soporte | soporte | 0.95 | si | ok | 0.27 | Mi pedido no llego |
| s06 | soporte | soporte | soporte | 0.95 | si | ok | 0.49 | Como cambio mi correo de acceso |
| s07 | soporte | soporte | soporte | 0.95 | si | ok | 0.63 | Factura con datos incorrectos |
| s08 | soporte | soporte | soporte | 0.95 | si | ok | 0.57 | Queja por el servicio |
| s09 | soporte | soporte | soporte | 0.95 | si | ok | 0.25 | La pagina no carga |
| s10 | soporte | soporte | soporte | 0.95 | si | ok | 0.49 | Cancelar mi suscripcion |
| s11 | soporte | soporte | soporte | 0.95 | si | ok | 0.84 | Falla en las notificaciones |
| s12 | soporte | soporte | soporte | 0.95 | si | ok | 0.54 | Producto llego danado |
| s13 | soporte | soporte | soporte | 0.95 | si | ok | 0.87 | Duda sobre como importar contactos |
| s14 | soporte | soporte | soporte | 0.95 | si | ok | 0.66 | Ticket 4521 sin respuesta |
| s15 | soporte | soporte | soporte | 0.95 | si | ok | 0.87 | Se perdieron mis datos |
| p01 | spam | spam | spam | 0.99 | si | ok | 0.54 | Felicidades, ganaste un premio |
| p02 | spam | spam | spam | 0.99 | si | ok | 0.95 | Inversion en cripto 100% garantizada |
| p03 | spam | spam | spam | 0.99 | si | ok | 0.83 | Posicionamiento SEO barato |
| p04 | spam | spam | spam | 0.99 | si | ok | 0.84 | Prestamo aprobado sin buro |
| p05 | spam | spam | spam | 0.99 | si | ok | 0.75 | Compra seguidores |
| p06 | spam | spam | spam | 0.99 | si | ok | 0.54 | Herencia millonaria |
| p07 | spam | spam | spam | 0.99 | si | ok | 0.73 | Viagra sin receta |
| p08 | spam | spam | incierto | 0.6 | NO | ok | 0.92 | asdf qwer |
| p09 | spam | spam | spam | 0.99 | si | ok | 0.68 | Gana dinero desde casa |
| p10 | spam | spam | spam | 0.99 | si | ok | 0.86 | Ultima oportunidad de lotería |
| d01 | dificil | soporte | soporte | 0.9 | si | ok | 0.56 | Problema con mi plan y mas licencias |
| d02 | dificil | ventas | ventas | 0.95 | si | ok | 1.33 | Pricing request |
| d03 | dificil | soporte | soporte | 0.95 | si | ok | 0.99 | Cannot log in |
| d04 | dificil | spam | ventas | 0.99 | NO | ok | 0.44 | Precio del plan Pro |
| d05 | dificil | soporte | soporte | 0.95 | si | ok | 0.56 | No puedo acceder |
| d06 | dificil | ventas | ventas | 0.95 | si | ok | 0.47 | Cotizacion urgente de sus servicios |
| d07 | dificil | ventas | ventas | 0.95 | si | ok | 0.76 | Re: Re: Re: Informacion |
| d08 | dificil | soporte | soporte | 0.95 | si | ok | 0.75 | Re: Re: Re: Re: sigo sin recibir mi pedido |
| d09 | dificil | spam | spam | 0.99 | si | ok | 0.63 | Aviso de seguridad de su cuenta |
| d10 | dificil | spam | spam | 0.95 | si | ok | 0.55 | Colaboracion para su negocio |
