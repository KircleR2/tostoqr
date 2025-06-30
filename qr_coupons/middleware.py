from django.shortcuts import redirect
from django.urls import resolve, reverse
from django.http import HttpResponseRedirect

class RedirectBranchAdminMiddleware:
    """
    Middleware para redirigir las solicitudes de la vista de administración de Branch
    a nuestra vista personalizada.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Procesar la solicitud antes de la vista
        if request.path == '/admin/qr_coupons/branch/':
            return HttpResponseRedirect(reverse('admin_branch'))
            
        if request.path.startswith('/admin/qr_coupons/branch/') and not request.path == '/admin/qr_coupons/branch/':
            # Extraer el ID de la sucursal de la URL
            try:
                branch_id = request.path.split('/')[-2]
                if branch_id.isdigit():
                    return HttpResponseRedirect(reverse('admin_branch_detail', kwargs={'branch_id': int(branch_id)}))
            except (IndexError, ValueError):
                pass
                
        response = self.get_response(request)
        return response 