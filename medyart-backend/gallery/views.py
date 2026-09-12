from rest_framework import permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response

class AccountUpdateView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def put(self, request):
        user = request.user
        action = request.data.get('action')

        if action == 'username':
            old_username = request.data.get('old_username')
            new_username = request.data.get('new_username')
            confirm_username = request.data.get('confirm_username')

            if user.username != old_username:
                return Response({"detail": "Current username does not match."}, status=status.HTTP_400_BAD_REQUEST)
            if new_username != confirm_username:
                return Response({"detail": "New usernames do not match."}, status=status.HTTP_400_BAD_REQUEST)
            
            user.username = new_username
            user.save()
            return Response({"message": "Username updated successfully."})

        elif action == 'password':
            old_password = request.data.get('old_password')
            new_password = request.data.get('new_password')
            confirm_password = request.data.get('confirm_password')

            if not user.check_password(old_password):
                return Response({"detail": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)
            if new_password != confirm_password:
                return Response({"detail": "New passwords do not match."}, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({"message": "Password updated successfully."})

        elif action == 'card':
            card_number = request.data.get('card_number')
            exp_date = request.data.get('exp_date')
            cvc = request.data.get('cvc')

            if not (card_number and exp_date and cvc):
                return Response({"detail": "Please fill out all credit card fields."}, status=status.HTTP_400_BAD_REQUEST)

            return Response({"message": "Credit card details saved successfully."})

        return Response({"detail": "Invalid action requested."}, status=status.HTTP_400_BAD_REQUEST)
