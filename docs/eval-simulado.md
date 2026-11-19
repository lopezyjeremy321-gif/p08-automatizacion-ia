# Evaluacion P08 - simulado (palabras clave)

- Casos: 50 (15 ventas, 15 soporte, 10 spam, 10 dificiles). Etiquetas escritas a mano ANTES de ejecutar el modelo.
- Aciertos exactos: **43/50 = 86.0 %** (1 repeticion).
- Margen: IC 95 % Wilson 73.8 % a 93.0 % (aprox. +-10 pts). Con 50 casos y 1 rep, diferencias menores a ese margen no son concluyentes.
- Cobertura (no 'incierto'): 88.0 %; exactitud entre los respondidos: 97.7 %.
- **Falso positivo de spam** (correo legitimo marcado como spam): 0/37 = 0.0 % 
- Latencia media por clasificacion: 0.0 s

## Matriz de confusion (filas = etiqueta humana, columnas = prediccion)

| real \ pred | ventas | soporte | spam | incierto |
|---|---|---|---|---|
| **ventas** | 16 | 0 | 0 | 2 |
| **soporte** | 0 | 17 | 0 | 2 |
| **spam** | 1 | 0 | 10 | 2 |

## Precision y recall

| clase | n real | precision | recall |
|---|---|---|---|
| ventas | 18 | 94.1 % | 88.9 % |
| soporte | 19 | 100.0 % | 89.5 % |
| spam | 13 | 100.0 % | 76.9 % |

## Por grupo

| grupo | aciertos |
|---|---|
| ventas | 15/15 |
| soporte | 14/15 |
| spam | 8/10 |
| dificil | 6/10 |

## Tabla de aciertos por caso

| id | grupo | real | pred | conf | ok | razon | lat s | asunto |
|---|---|---|---|---|---|---|---|---|
| v01 | ventas | ventas | ventas | 0.95 | si | ok | 0.0 | Cotizacion para mi oficina |
| v02 | ventas | ventas | ventas | 0.85 | si | ok | 0.0 | Demo del servicio |
| v03 | ventas | ventas | ventas | 0.95 | si | ok | 0.0 | Precio mayorista |
| v04 | ventas | ventas | ventas | 0.75 | si | ok | 0.0 | Cuanto cuesta el plan anual |
| v05 | ventas | ventas | ventas | 0.75 | si | ok | 0.0 | Propuesta para restaurante |
| v06 | ventas | ventas | ventas | 0.85 | si | ok | 0.0 | Quiero adquirir licencias |
| v07 | ventas | ventas | ventas | 0.95 | si | ok | 0.0 | Informacion de planes |
| v08 | ventas | ventas | ventas | 0.75 | si | ok | 0.0 | Consulta comercial |
| v09 | ventas | ventas | ventas | 0.65 | si | ok | 0.0 | Plan para freelancers |
| v10 | ventas | ventas | ventas | 0.75 | si | ok | 0.0 | Presupuesto de implementacion |
| v11 | ventas | ventas | ventas | 0.75 | si | ok | 0.0 | Me interesa su producto |
| v12 | ventas | ventas | ventas | 0.75 | si | ok | 0.0 | Cotizar renovacion con mas usuarios |
| v13 | ventas | ventas | ventas | 0.75 | si | ok | 0.0 | Alianza y precios para revendedores |
| v14 | ventas | ventas | ventas | 0.95 | si | ok | 0.0 | Pregunta antes de comprar |
| v15 | ventas | ventas | ventas | 0.95 | si | ok | 0.0 | Solicitud de demo y tarifas |
| s01 | soporte | soporte | soporte | 0.95 | si | ok | 0.0 | No puedo entrar a mi cuenta |
| s02 | soporte | soporte | soporte | 0.75 | si | ok | 0.0 | Error al exportar reportes |
| s03 | soporte | soporte | soporte | 0.85 | si | ok | 0.0 | Cobro duplicado |
| s04 | soporte | soporte | soporte | 0.75 | si | ok | 0.0 | La aplicacion se cierra sola |
| s05 | soporte | soporte | soporte | 0.65 | si | ok | 0.0 | Mi pedido no llego |
| s06 | soporte | soporte | soporte | 0.65 | si | ok | 0.0 | Como cambio mi correo de acceso |
| s07 | soporte | soporte | soporte | 0.75 | si | ok | 0.0 | Factura con datos incorrectos |
| s08 | soporte | soporte | soporte | 0.75 | si | ok | 0.0 | Queja por el servicio |
| s09 | soporte | soporte | soporte | 0.85 | si | ok | 0.0 | La pagina no carga |
| s10 | soporte | soporte | soporte | 0.75 | si | ok | 0.0 | Cancelar mi suscripcion |
| s11 | soporte | soporte | soporte | 0.75 | si | ok | 0.0 | Falla en las notificaciones |
| s12 | soporte | soporte | soporte | 0.75 | si | ok | 0.0 | Producto llego danado |
| s13 | soporte | soporte | incierto | 0.0 | NO | sin_senales | 0.0 | Duda sobre como importar contactos |
| s14 | soporte | soporte | soporte | 0.85 | si | ok | 0.0 | Ticket 4521 sin respuesta |
| s15 | soporte | soporte | soporte | 0.65 | si | ok | 0.0 | Se perdieron mis datos |
| p01 | spam | spam | spam | 0.95 | si | ok | 0.0 | Felicidades, ganaste un premio |
| p02 | spam | spam | spam | 0.95 | si | ok | 0.0 | Inversion en cripto 100% garantizada |
| p03 | spam | spam | spam | 0.65 | si | ok | 0.0 | Posicionamiento SEO barato |
| p04 | spam | spam | spam | 0.75 | si | ok | 0.0 | Prestamo aprobado sin buro |
| p05 | spam | spam | spam | 0.95 | si | ok | 0.0 | Compra seguidores |
| p06 | spam | spam | spam | 0.75 | si | ok | 0.0 | Herencia millonaria |
| p07 | spam | spam | incierto | 0.4 | NO | empate | 0.0 | Viagra sin receta |
| p08 | spam | spam | incierto | 0.0 | NO | sin_senales | 0.0 | asdf qwer |
| p09 | spam | spam | spam | 0.75 | si | ok | 0.0 | Gana dinero desde casa |
| p10 | spam | spam | spam | 0.75 | si | ok | 0.0 | Ultima oportunidad de lotería |
| d01 | dificil | soporte | soporte | 0.65 | si | ok | 0.0 | Problema con mi plan y mas licencias |
| d02 | dificil | ventas | incierto | 0.0 | NO | sin_senales | 0.0 | Pricing request |
| d03 | dificil | soporte | soporte | 0.65 | si | ok | 0.0 | Cannot log in |
| d04 | dificil | spam | ventas | 0.75 | NO | ok | 0.0 | Precio del plan Pro |
| d05 | dificil | soporte | soporte | 0.75 | si | ok | 0.0 | No puedo acceder |
| d06 | dificil | ventas | ventas | 0.65 | si | ok | 0.0 | Cotizacion urgente de sus servicios |
| d07 | dificil | ventas | incierto | 0.0 | NO | sin_senales | 0.0 | Re: Re: Re: Informacion |
| d08 | dificil | soporte | incierto | 0.0 | NO | sin_senales | 0.0 | Re: Re: Re: Re: sigo sin recibir mi pedido |
| d09 | dificil | spam | spam | 0.85 | si | ok | 0.0 | Aviso de seguridad de su cuenta |
| d10 | dificil | spam | spam | 0.75 | si | ok | 0.0 | Colaboracion para su negocio |
