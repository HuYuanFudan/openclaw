from rest_framework.permissions import BasePermission
import logging

logger = logging.getLogger(__name__)
class IsMetaKnowledgeUser(BasePermission):
    def has_permission(self, request, view):
        return request.user.user_type == 'metaknowledge'

class IsNeo4jUser(BasePermission):
    def has_permission(self, request, view):
        # 检查用户是否已经通过身份验证，并且 user_type 是 'neo4j'
        return request.user.is_authenticated and request.user.user_type == 'neo4j'