from django.shortcuts import render, reverse, HttpResponseRedirect
from django.http import FileResponse, HttpResponse
from urllib import parse
from django.contrib.auth.models import User
from MachLab.models import Userinfo, Model, Modelfile, ModelResult, ModelCommit, ModelPush, ModelPull, ModelDrop, Comment, Star
from django import forms
from django.forms import widgets
from MachLab.settings import BASE_DIR
from MachLab.public import *
from MachLab.record import *

def models(request, username, model_name):
    context = {}
    context['title'] = '模型仓库 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    context['active'] = 'files'
    record_click(request, username, model_name)
    get_model_info(context, request, username, model_name)
    return render(request, 'files.html', context)

def modelfile(request, username, model_name, modelfile_filename):
    context = {}
    context['title'] = '模型仓库 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    context['modelfile_filename'] = modelfile_filename
    context['active'] = 'files'
    model, modelfile = get_model_modelfile(username, model_name, modelfile_filename)
    context['model'] = model
    context['modelfile'] = modelfile
    get_model_info(context, request, username, model_name)
    return render(request, 'modelfile.html', context)

def modelfile_delete(request, username, model_name, modelfile_filename):
    context = {}
    context['title'] = '模型仓库 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    context['modelfile_filename'] = modelfile_filename
    context['active'] = 'files'
    delete_modelfile(username, model_name, modelfile_filename)
    get_model_info(context, request, username, model_name)
    return render(request, 'files.html', context)

def comments(request, username, model_name):
    context = {}
    context['title'] = '模型评论 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    context['active'] = 'comments'
    user = User.objects.get(username=username)
    model = Model.objects.filter(user=user, model_name=model_name).first()
    get_model_info(context, request, username, model_name)
    get_comment_list(context, model)
    return render(request, 'comments.html', context)

def insights(request, username, model_name):
    context = {}
    context['title'] = '模型结果 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    context['active'] = 'insights'
    get_model_info(context, request, username, model_name)
    return render(request, 'insights.html', context)

def insights_display(request, username, model_name, selected_filename):
    context = {}
    context['title'] = '模型结果 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    context['selected_filename'] = selected_filename
    context['active'] = 'insights'
    result_file = Modelfile.objects.filter(filename=selected_filename).first()
    result_data = result_file.file.read()
    context['result_file'] = result_file
    context['result_data'] = result_data
    context['resultAvailable'] = True
    get_model_info(context, request, username, model_name)
    return render(request, 'insights.html', context)

class ModelSettingsForm(forms.Form):
    model_name = forms.CharField(max_length=32,widget=widgets.Input(attrs={'class':"form-control"}))
    model_type = forms.ChoiceField(choices=model_type_choices,widget=widgets.Select(attrs={'class':"form-control"}))
    description = forms.CharField(max_length=256, required=False,widget=widgets.Textarea(attrs={'class':"form-control wid-full"}))
    
    def set_initial_fields(self, model=None):
        if model:
            self.fields['model_name'].initial = model.model_name
            self.fields['model_type'].initial = model.model_type
            self.fields['description'].initial = model.description

def settings(request, username, model_name):
    context = {}
    context['title'] = '模型设置 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    context['active'] = 'settings'

    if request.user.username == username:
        if request.method == 'POST':
            redirect_to = request.POST.get('next', request.GET.get('next',''))
            form = ModelSettingsForm(request.POST)
            context['form'] = form
            if form.is_valid():
                cd = form.cleaned_data
                new_model_name = cd['model_name']
                new_model_type = cd['model_type']
                new_description = cd['description']
            
                model = Model.objects.filter(model_name=model_name).first()

                if model is not None:
                    new_model = Model.objects.filter(model_name=new_model_name).first()
                    if model != new_model:
                        context['alreadyExisted'] = True
                    else:
                        model.model_name = new_model_name
                        model.model_type = new_model_type
                        model.description = new_description
                        model.save()
                    get_model_info(context, request, username, new_model_name)
                    return render(request, 'settings.html', context)
                else:
                    new_model = Model.objects.create(model_name=new_model_name, model_type=new_model_type, description=new_description)
                    new_model.save()
                    get_model_info(context, request, username, model_name)
                    return render(request, 'settings.html', context)
        else:
            model = Model.objects.filter(model_name=model_name).first()
            form = ModelSettingsForm()
            form.set_initial_fields(model)
            context['form'] = form
            get_model_info(context, request, username, model_name)
            return render(request, 'settings.html', context)
    else:
        return HttpResponseRedirect('/')

def modelfile_upload(request, username, model_name):
    context = {}
    context['title'] = '上传 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    redirect_to = request.POST.get('next', request.GET.get('next',''))
    upload_file = request.FILES.get('upload_file')
    upload_modelfile(request.user.username, model_name, upload_file)
    get_model_info(context, request, username, model_name)
    return render(request, 'files.html', context)

def model_download(request, username, model_name):
    context = {}
    context['title'] = '下载 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    redirect_to = request.POST.get('next', request.GET.get('next',''))
    data = download_model(request.user.username, username, model_name)
    if data:
        response = HttpResponse(data, content_type='application/zip')  
        response['Content-Type'] = 'application/octet-stream'  
        response['Content-Disposition'] = 'attachment;filename=' + parse.quote(model_name)
        return response

def model_create(request, username):
    context = {}
    context['title'] = '创建模型 | MachLab'
    context['username'] = username
    context['active'] = 'files'

    if request.user.username == username:
        if request.method == 'POST':
            redirect_to = request.POST.get('next', request.GET.get('next',''))
            form = ModelSettingsForm(request.POST)
            context['form'] = form
            if form.is_valid():
                cd = form.cleaned_data
                new_model_name = cd['model_name']
                new_model_type = cd['model_type']
                new_description = cd['description']
            
                model = Model.objects.filter(model_name=new_model_name).first()

                if model is not None:
                    context['alreadyExisted'] = True
                    return render(request, 'new.html', context)
                    #return HttpResponseRedirect(reverse('user-profile', args=(request.user.username,)))
                else:
                    user = User.objects.get(username=request.user.username)
                    new_model = Model.objects.create(user=user, model_name=new_model_name, model_type=new_model_type, description=new_description)
                    new_model.save()
                    get_model_info(context, request, request.user.username, new_model_name)
                    return render(request, 'files.html', context)
        else:
            form = ModelSettingsForm()
            context['form'] = form
            return render(request, 'new.html', context)
    else:
        return HttpResponseRedirect('/')

def model_delete(request, username, model_name):
    context = {}
    context['title'] = '删除模型 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    redirect_to = request.POST.get('next', request.GET.get('next',''))
    user = User.objects.get(username=request.user.username)
    model = Model.objects.filter(user=user, model_name=model_name).delete()
    return HttpResponseRedirect(redirect_to)

def star(request, username, model_name):
    context = {}
    context['title'] = '点赞 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    context['active'] = 'files'
    redirect_to = request.POST.get('next', request.GET.get('next',''))
    record_star(request, username, model_name)
    return HttpResponseRedirect(redirect_to)

def unstar(request, username, model_name):
    context = {}
    context['title'] = '取消点赞 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    context['active'] = 'files'
    redirect_to = request.POST.get('next', request.GET.get('next',''))
    record_unstar(request, username, model_name)
    return HttpResponseRedirect(redirect_to)

def comment_new(request, username, model_name):
    context = {}
    context['title'] = '新建评论 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    context['active'] = 'comments'
    target_id = request.POST.get('new-comment-target-id')
    content = request.POST.get('comment-body')
    model = record_new_comment(request.user.username, username, model_name, target_id, content)
    get_model_info(context, request, username, model_name)
    get_comment_list(context, model)
    return render(request, 'comments.html', context)

def comment_delete(request, username, model_name):
    context = {}
    context['title'] = '删除评论 | MachLab'
    context['username'] = username
    context['model_name'] = model_name
    context['active'] = 'comments'
    model = Model.objects.get(model_name=model_name)
    comment_id = request.POST.get('comment-to-delete-id')
    record_delete_comment(comment_id)
    get_model_info(context, request, username, model_name)
    get_comment_list(context, model)
    return render(request, 'comments.html', context)

def ranking_list(request):
    context = {}
    context['title'] = '模型精选 | MachLab'
    context['q'] = 'RankingList'
    context['type'] = 'RankingList'
    context['n_top'] = n_top
    models = get_n_top(n_top)
    context['models'] = models
    return render(request, 'search.html', context)