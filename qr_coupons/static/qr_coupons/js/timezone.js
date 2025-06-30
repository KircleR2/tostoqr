/**
 * Script para convertir fechas UTC a la zona horaria local del usuario
 */
document.addEventListener('DOMContentLoaded', function() {
    // Buscar todos los elementos con la clase 'local-datetime'
    const datetimeElements = document.querySelectorAll('.local-datetime');
    
    datetimeElements.forEach(function(element) {
        // Obtener el valor UTC de data-datetime
        const utcDatetime = element.getAttribute('data-datetime');
        
        if (utcDatetime) {
            try {
                // Convertir a objeto Date
                const date = new Date(utcDatetime);
                
                // Formatear la fecha según el formato especificado
                const format = element.getAttribute('data-format') || 'DD/MM/YYYY HH:mm';
                
                // Formatear la fecha en la zona horaria local
                const formattedDate = formatDate(date, format);
                
                // Actualizar el contenido del elemento
                element.textContent = formattedDate;
            } catch (error) {
                console.error('Error al convertir la fecha:', error);
            }
        }
    });
});

/**
 * Formatea una fecha según el formato especificado
 * @param {Date} date - Objeto Date a formatear
 * @param {string} format - Formato deseado (DD/MM/YYYY HH:mm, etc.)
 * @returns {string} - Fecha formateada
 */
function formatDate(date, format) {
    const day = String(date.getDate()).padStart(2, '0');
    const month = String(date.getMonth() + 1).padStart(2, '0');
    const year = date.getFullYear();
    const hours = String(date.getHours()).padStart(2, '0');
    const minutes = String(date.getMinutes()).padStart(2, '0');
    const seconds = String(date.getSeconds()).padStart(2, '0');
    
    // Reemplazar tokens en el formato
    return format
        .replace('DD', day)
        .replace('MM', month)
        .replace('YYYY', year)
        .replace('HH', hours)
        .replace('mm', minutes)
        .replace('ss', seconds);
} 