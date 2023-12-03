from django.http import JsonResponse, Http404
from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from .forms import CompanyForm, DomainForm
from .models import Company, Domain
from django.views import View
import requests, json
from datetime import datetime, date, timedelta

# Create your views here.

def index(request):
    return render(request, "index.html")

def dashboard(request):
    active_domains = Domain.objects.filter(expiry_date__gte=date.today()).count()
    expired_domains = Domain.objects.filter(expiry_date__lt=date.today()).count()

    context = {
        'active_domains': active_domains,
        'expired_domains': expired_domains,
    }

    return render(request, 'dashboard.html', context)

def signin(request):
    msg = ""
    if request.method == "POST":
        username = request.POST['username'] 
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            
            if "next" in request.POST:
                return redirect(request.POST.get("next"))
            return redirect("dashboard")
        else:
            msg = "Invalid credentials"
    context = {"msg": msg}
    return render(request, "signin.html", context)

def signup(request):
    
    form = UserCreationForm()
    if request.method == 'POST':
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            # login starts here
            username = request.POST['username'] 
            password = request.POST['password1']
            user = authenticate(request, username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("index")
    context = {"form":form}
    return render(request, "signup.html", context)

def signout(request):
    logout(request)
    return redirect("index")

def company_list(request, id=0):
    if request.method == "GET":
        if id==0:
            form = CompanyForm()
        else:
            company = Company.objects.get(pk=id)
            form = CompanyForm(instance=company)
        return render(request, "manage_company.html",{'form':form})
    else:
        if id == 0:
            form = CompanyForm(request.POST)
        else:
            company = Company.objects.get(pk=id)   
            form = CompanyForm(request.POST,instance=company) 
        if form.is_valid():
            form.save()
            context = {'companies': Company.objects.all()}
        return render(request, "company_list.html", context)
    
def companies(request):
    context = {'companies': Company.objects.all()} 
    return render(request,"company_list.html", context)

def company_delete(request, id):
    company = Company.objects.get(pk=id)
    company.delete()
    return(redirect('lists'))

def domain(request):
    context = {'domains': Domain.objects.all()}
    return render(request, "manage_domain.html", context)

def domain_status(request):
    context = {'domains': Domain.objects.all()}
    return render(request, "domain_status.html", context)

def domain_list(request):
    if request.method == "GET":
        form = DomainForm()
        return render(request, "add_domain.html",{'form':form})
    else:
        form = DomainForm(request.POST)
        if form.is_valid():
            form.save()
            context = {'domains': Domain.objects.all()}
        return render(request, "manage_domain.html", context)

def lookup(request):
    if request.method == 'POST':
        form = DomainForm(request.POST)
        
        if form.is_valid():
            try:
                domain_value = form.cleaned_data['name']
                
                print(f"Domain Value: {domain_value}")

                # Your API token for whoisjsonapi.com
                api_token = 'FQcwBdbvYkjMHFZ6B4HEVnOovTnS07CUqRnR26NAJcxWCx6yTNrfUzN9YUzE_eC'
                
                # Construct the API URL
                api_url = f'https://whoisjsonapi.com/v1/{domain_value}'
                print(f"api_url: {api_url}")
                # Set the headers for the request
                headers = {

                    'Authorization': f'Bearer {api_token}',
                }
                
                # Send a GET request to the API with headers and timeout
                response = requests.get(api_url, headers=headers)
                
                # Check if the API request was successful
                response.raise_for_status()
                
                # Parse the JSON response
                data = response.json()
                
                print(f"API Response: {response.content}")
                
                # Extract relevant information
                domain_info = data.get('domain', {})
                registration_date = domain_info.get('created_date', '')
                expiry_date = domain_info.get('expiration_date', '')
                
                print(f"Creation Date: {registration_date}")
                print(f"Expiration Date: {expiry_date}")

                # Return the relevant data as JSON
                return JsonResponse({
                    'status': 'success',
                    'registration_date': registration_date,
                    'expiry_date': expiry_date,
                })
            
            except requests.RequestException as e:
                # Handle API request error
                return JsonResponse({'error': f'Failed to retrieve data from the API. Error: {e}'}, status=500)
            
            except Exception as e:
                # Handle other exceptions
                return JsonResponse({'error': f'An unexpected error occurred: {e}'}, status=500)
        
        else:
            # Handle form validation errors
            return JsonResponse({'error': 'Form validation error.'}, status=400)
    
    else:
        return JsonResponse({'error': 'This view is for handling POST requests only.'}, status=400)
    
class DomainUpdateView(View):
    def get(self, request, *args, **kwargs):
        domain_name = self.kwargs.get('domain_name')
        api_token = 'FQcwBdbvYkjMHFZ6B4HEVnOovTnS07CUqRnR26NAJcxWCx6yTNrfUzN9YUzE_eC'  # Replace with your actual API token

        # Print the URL before making the API request
        print(f'Requesting API for domain: {domain_name}')
        api_url = f'https://whoisjsonapi.com/v1/{domain_name}'
        print(f"api_url: {api_url}")

        # Set the headers for the request
        headers = {
             'Authorization': f'Bearer {api_token}',
        }

        try:
            # Make the API request
            response = requests.get(api_url, headers=headers)
            response.raise_for_status()  # Check if the API request was successful

            # Parse the JSON response
            data = response.json()
            print(f"API Response: {response.content}")

            # Check if the response has the expected structure
            if 'domain' not in data:
                raise ValueError('Invalid response structure')

            # Extract relevant information
            domain_info = data['domain']
            updated_date_str = domain_info.get('updated_date', '')

            # Attempt to convert the updated_date string to a formatted date
            try:
                # Try parsing with milliseconds
                updated_date = datetime.strptime(updated_date_str, "%Y-%m-%dT%H:%M:%S.%fZ")
            except ValueError:
                try:
                    # Try parsing without milliseconds
                    updated_date = datetime.strptime(updated_date_str, "%Y-%m-%dT%H:%M:%SZ")
                except ValueError:
                    # If both parsing attempts fail, set updated_date to None
                    updated_date = None

            # Check if updated_date is set
            if updated_date:
                # Format the date with the desired format
                formatted_date = updated_date.strftime("%B %d, %Y, %I %p")
                print(f"Formatted Updated Date: {formatted_date}")
            else:
                formatted_date = 'N/A'
                print(f"Updated Date: {formatted_date}")

            # Respond with the formatted updated_date
            return JsonResponse({'updated_date': formatted_date})

        except requests.exceptions.RequestException as e:
            # Handle request exceptions
            print(f'Error for {domain_name}: {str(e)}')
            return JsonResponse({'error': str(e)}, status=500)

        except ValueError as e:
            # Handle invalid response structure
            print(f'Error for {domain_name}: {str(e)}')
            return JsonResponse({'error': str(e)}, status=500)
        

def domain_delete(request, id):
    try:
        # Retrieve the Domain object with the given id
        domain = get_object_or_404(Domain, pk=id)
        
        # Delete the Domain object
        domain.delete()
        
        # Redirect to the domain list page after deletion
        return redirect('domain')
    
    except Domain.DoesNotExist:
        # Handle the case where the Domain object does not exist
        raise Http404("Domain does not exist")
        
