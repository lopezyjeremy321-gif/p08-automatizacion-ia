# Evaluacion P08 - ollama:llama3.2:3b

- Casos: 50 (15 ventas, 15 soporte, 10 spam, 10 dificiles). Etiquetas escritas a mano ANTES de ejecutar el modelo.
- Aciertos exactos: **47/50 = 94.0 %** (1 repeticion).
- Margen: IC 95 % Wilson 83.8 % a 97.9 % (aprox. +-7 pts). Con 50 casos y 1 rep, diferencias menores a ese margen no son concluyentes.
- Cobertura (no 'incierto'): 94.0 %; exactitud entre los respondidos: 100.0 %.
- **Falso positivo de spam** (correo legitimo marcado como spam): 0/37 = 0.0 % 
- Latencia media por clasificacion: 2.42 s

## Matriz de confusion (filas = etiqueta humana, columnas = prediccion)

| real \ pred | ventas | soporte | spam | incierto |
|---|---|---|---|---|
| **ventas** | 18 | 0 | 0 | 0 |
| **soporte** | 0 | 19 | 0 | 0 |
| **spam** | 0 | 0 | 10 | 3 |

## Precision y recall

| clase | n real | precision | recall |
|---|---|---|---|
| ventas | 18 | 100.0 % | 100.0 % |
| soporte | 19 | 100.0 % | 100.0 % |
| spam | 13 | 100.0 % | 76.9 % |

## Por grupo

| grupo | aciertos |
|---|---|
| ventas | 15/15 |
| soporte | 15/15 |
| spam | 8/10 |
| dificil | 9/10 |

## Tabla de aciertos por caso

| id | grupo | real | pred | conf | ok | razon | lat s | asunto |
|---|---|---|---|---|---|---|---|---|
| v01 | ventas | ventas | ventas | 0.9 | si | ok | 2.01 | Cotizacion para mi oficina |
| v02 | ventas | ventas | ventas | 0.9 | si | ok | 1.79 | Demo del servicio |
| v03 | ventas | ventas | ventas | 0.9 | si | ok | 1.52 | Precio mayorista |
| v04 | ventas | ventas | ventas | 0.9 | si | ok | 2.2 | Cuanto cuesta el plan anual |
| v05 | ventas | ventas | ventas | 0.9 | si | ok | 1.9 | Propuesta para restaurante |
| v06 | ventas | ventas | ventas | 0.9 | si | ok | 0.85 | Quiero adquirir licencias |
| v07 | ventas | ventas | ventas | 0.9 | si | ok | 2.38 | Informacion de planes |
| v08 | ventas | ventas | ventas | 0.9 | si | ok | 1.85 | Consulta comercial |
| v09 | ventas | ventas | ventas | 0.9 | si | ok | 1.69 | Plan para freelancers |
| v10 | ventas | ventas | ventas | 0.9 | si | ok | 1.95 | Presupuesto de implementacion |
| v11 | ventas | ventas | ventas | 0.9 | si | ok | 1.52 | Me interesa su producto |
| v12 | ventas | ventas | ventas | 0.9 | si | ok | 1.75 | Cotizar renovacion con mas usuarios |
| v13 | ventas | ventas | ventas | 0.9 | si | ok | 1.59 | Alianza y precios para revendedores |
| v14 | ventas | ventas | ventas | 0.9 | si | ok | 2.88 | Pregunta antes de comprar |
| v15 | ventas | ventas | ventas | 0.9 | si | ok | 2.13 | Solicitud de demo y tarifas |
| s01 | soporte | soporte | soporte | 0.9 | si | ok | 2.41 | No puedo entrar a mi cuenta |
| s02 | soporte | soporte | soporte | 0.9 | si | ok | 2.3 | Error al exportar reportes |
| s03 | soporte | soporte | soporte | 0.9 | si | ok | 1.54 | Cobro duplicado |
| s04 | soporte | soporte | soporte | 0.9 | si | ok | 1.72 | La aplicacion se cierra sola |
| s05 | soporte | soporte | soporte | 0.9 | si | ok | 2.13 | Mi pedido no llego |
| s06 | soporte | soporte | soporte | 0.9 | si | ok | 1.74 | Como cambio mi correo de acceso |
| s07 | soporte | soporte | soporte | 0.9 | si | ok | 2.19 | Factura con datos incorrectos |
| s08 | soporte | soporte | soporte | 0.9 | si | ok | 3.95 | Queja por el servicio |
| s09 | soporte | soporte | soporte | 0.9 | si | ok | 3.11 | La pagina no carga |
| s10 | soporte | soporte | soporte | 0.9 | si | ok | 2.58 | Cancelar mi suscripcion |
| s11 | soporte | soporte | soporte | 0.9 | si | ok | 1.62 | Falla en las notificaciones |
| s12 | soporte | soporte | soporte | 1.0 | si | ok | 3.14 | Producto llego danado |
| s13 | soporte | soporte | soporte | 0.9 | si | ok | 5.69 | Duda sobre como importar contactos |
| s14 | soporte | soporte | soporte | 0.9 | si | ok | 4.29 | Ticket 4521 sin respuesta |
| s15 | soporte | soporte | soporte | 0.9 | si | ok | 1.76 | Se perdieron mis datos |
| p01 | spam | spam | spam | 0.9 | si | ok | 2.21 | Felicidades, ganaste un premio |
| p02 | spam | spam | spam | 0.9 | si | ok | 1.17 | Inversion en cripto 100% garantizada |
| p03 | spam | spam | spam | 0.9 | si | ok | 1.84 | Posicionamiento SEO barato |
| p04 | spam | spam | incierto | 0.8 | NO | ok | 4.8 | Prestamo aprobado sin buro |
| p05 | spam | spam | spam | 0.9 | si | ok | 1.95 | Compra seguidores |
| p06 | spam | spam | incierto | 0.8 | NO | ok | 1.97 | Herencia millonaria |
| p07 | spam | spam | spam | 0.9 | si | ok | 1.83 | Viagra sin receta |
| p08 | spam | spam | spam | 0.9 | si | ok | 1.75 | asdf qwer |
| p09 | spam | spam | spam | 0.9 | si | ok | 2.42 | Gana dinero desde casa |
| p10 | spam | spam | spam | 0.9 | si | ok | 1.24 | Ultima oportunidad de lotería |
| d01 | dificil | soporte | soporte | 0.9 | si | ok | 0.82 | Problema con mi plan y mas licencias |
| d02 | dificil | ventas | ventas | 0.9 | si | ok | 2.02 | Pricing request |
| d03 | dificil | soporte | soporte | 0.9 | si | ok | 2.2 | Cannot log in |
| d04 | dificil | spam | incierto | 0.0 | NO | ok | 1.76 | Precio del plan Pro |
| d05 | dificil | soporte | soporte | 0.9 | si | ok | 2.83 | No puedo acceder |
| d06 | dificil | ventas | ventas | 1.0 | si | ok | 2.2 | Cotizacion urgente de sus servicios |
| d07 | dificil | ventas | ventas | 0.9 | si | ok | 6.87 | Re: Re: Re: Informacion |
| d08 | dificil | soporte | soporte | 0.9 | si | ok | 4.9 | Re: Re: Re: Re: sigo sin recibir mi pedido |
| d09 | dificil | spam | spam | 0.9 | si | ok | 4.09 | Aviso de seguridad de su cuenta |
| d10 | dificil | spam | spam | 0.9 | si | ok | 3.91 | Colaboracion para su negocio |
