from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate, login, logout
from django.db.models import Q

from .models import User, UserActivity
from .serializers import (
    UserSerializer, UserDetailSerializer, UserActivitySerializer,
    LoginSerializer, ChangePasswordSerializer
)


class LoginAPIView(APIView):
    """API endpoint for user login"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(username=username, password=password)
            
            if user:
                if user.is_active_employee:
                    token, created = Token.objects.get_or_create(user=user)
                    
                    
                    UserActivity.objects.create(
                        user=user,
                        action='login',
                        description=f'API login: {username}',
                        ip_address=self.get_client_ip(request)
                    )
                    
                    return Response({
                        'success': True,
                        'token': token.key,
                        'user': UserDetailSerializer(user).data
                    })
                else:
                    return Response({
                        'success': False,
                        'error': 'Account is deactivated'
                    }, status=status.HTTP_403_FORBIDDEN)
            else:
                return Response({
                    'success': False,
                    'error': 'Invalid credentials'
                }, status=status.HTTP_401_UNAUTHORIZED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class LogoutAPIView(APIView):
    """API endpoint for user logout"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            UserActivity.objects.create(
                user=request.user,
                action='logout',
                description='API logout'
            )
            
            request.user.auth_token.delete()
            
            return Response({
                'success': True,
                'message': 'Logged out successfully'
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class UserViewSet(viewsets.ModelViewSet):
    """ViewSet for User management"""
    queryset = User.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return UserDetailSerializer
        return UserSerializer
    
    def get_queryset(self):
        queryset = User.objects.all()
        
        
        role = self.request.query_params.get('role')
        if role:
            queryset = queryset.filter(role=role)
        
        
        is_active = self.request.query_params.get('is_active')
        if is_active:
            queryset = queryset.filter(is_active_employee=is_active.lower() == 'true')
        
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search) |
                Q(email__icontains=search)
            )
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        """Get current user profile"""
        serializer = UserDetailSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        """Change user password"""
        user = self.get_object()
        
        
        if user != request.user and request.user.role not in ['admin', 'manager']:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ChangePasswordSerializer(data=request.data)
        if serializer.is_valid():
            if user == request.user:
                if not user.check_password(serializer.validated_data['current_password']):
                    return Response({
                        'error': 'Current password is incorrect'
                    }, status=status.HTTP_400_BAD_REQUEST)
            
            
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            
            UserActivity.objects.create(
                user=user,
                action='update',
                description='Password changed via API'
            )
            
            return Response({
                'success': True,
                'message': 'Password changed successfully'
            })
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def activity(self, request, pk=None):
        """Get user activity log"""
        user = self.get_object()
        activities = UserActivity.objects.filter(user=user).order_by('-timestamp')[:50]
        serializer = UserActivitySerializer(activities, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Activate/deactivate user"""
        if request.user.role not in ['admin', 'manager']:
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user = self.get_object()
        user.is_active_employee = not user.is_active_employee
        user.save()
        
        action_text = 'activated' if user.is_active_employee else 'deactivated'
        
        
        UserActivity.objects.create(
            user=request.user,
            action='update',
            description=f'{action_text} user: {user.username}'
        )
        
        return Response({
            'success': True,
            'message': f'User {action_text} successfully',
            'is_active': user.is_active_employee
        })


class UserActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for viewing user activities"""
    queryset = UserActivity.objects.all()
    serializer_class = UserActivitySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = UserActivity.objects.all()
        
        
        user_id = self.request.query_params.get('user')
        if user_id:
            queryset = queryset.filter(user_id=user_id)
        
        
        action = self.request.query_params.get('action')
        if action:
            queryset = queryset.filter(action=action)
        
        return queryset.order_by('-timestamp')


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def refresh_token(request):
    """Refresh authentication token"""
    try:
        request.user.auth_token.delete()
        
        
        token = Token.objects.create(user=request.user)
        
        return Response({
            'success': True,
            'token': token.key
        })
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
