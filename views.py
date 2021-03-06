from datetime import date

from bubles_framework.templator import render
from patterns.сreational_patterns import Engine, Logger, MapperRegistry
from patterns.structural_patterns import AddRoute, DebugMethod
from patterns.behavioral_patterns import EmailNotifier, SmsNotifier, TemplateView, ListView, CreateView, BaseSerializer
from patterns.datamapper_patterns import UnitOfWork


site = Engine()
logger = Logger('main')
email_notifier = EmailNotifier()
sms_notifier = SmsNotifier()
UnitOfWork.new_current()
UnitOfWork.get_current().set_mapper_registry(MapperRegistry)

routes={}

@AddRoute(routes=routes, url='/')
class Index:
    @DebugMethod(name='Index')
    def __call__(self, request):
        return '200 OK', render('index.html', objects_list=site.categories)

@AddRoute(routes=routes, url='/about/')
class About:
    @DebugMethod(name='About')
    def __call__(self, request):
        return '200 OK', render('about.html')


@AddRoute(routes=routes, url='/study_programs/')
class StudyPrograms:
    @DebugMethod(name='StudyPrograms')
    def __call__(self, request):
        return '200 OK', render('study-programs.html', data=date.today())


class NotFound404:
    @DebugMethod(name='NotFound404')
    def __call__(self, request):
        return '404 WHAT', render('page_not_found_404.html')

"""
@AddRoute(routes=routes, url='/courses-list/')
class CoursesList(ListView):
    template_name = 'course_list.html'

    def get_queryset(self):
        mapper = MapperRegistry.get_current_mapper('course')
        return mapper.all()
"""
@AddRoute(routes=routes, url='/courses-list/')
class CoursesList:
    @DebugMethod(name='CoursesList')
    def __call__(self, request):
        logger.log('Список курсов')
        try:
            # category = site.find_category_by_id(int(request['request_params']['id']))
            category = site.find_category_by_id_mapper(int(request['request_params']['id']))
            print(f'category.courses={category.courses} | category.name={category.name} | category.id={category.id}')
            return '200 OK', render('course_list.html', objects_list=category.courses, name=category.name, id=category.id)
        except KeyError:
            return '200 OK', 'No courses have been added yet'


@AddRoute(routes=routes, url='/create-course/')
class CreateCourse:
    category_id = -1

    @DebugMethod(name='CreateCourse')
    def __call__(self, request):
        if request['method'] == 'POST':
            # метод пост
            data = request['data']

            name = data['name']
            name = site.decode_value(name)

            category = None
            if self.category_id != -1:
                category = site.find_category_by_id(int(self.category_id))

                course = site.create_course('record', name, category)
                # Добавляем наблюдателей на курс
                course.observers.append(email_notifier)
                course.observers.append(sms_notifier)
                site.courses.append(course)

            return '200 OK', render('course_list.html', objects_list=category.courses,
                                    name=category.name, id=category.id)
        else:
            try:
                self.category_id = int(request['request_params']['id'])
                category = site.find_category_by_id(int(self.category_id))

                return '200 OK', render('create_course.html', name=category.name, id=category.id)
            except KeyError:
                return '200 OK', 'No categories have been added yet'


@AddRoute(routes=routes, url='/copy-course/')
class CopyCourse:
    @DebugMethod(name='CopyCourse')
    def __call__(self, request):
        request_params = request['request_params']

        try:
            name = request_params['name']
            old_course = site.get_course(name)
            if old_course:
                new_name = f'copy_{name}'
                new_course = old_course.clone()
                new_course.name = new_name
                site.courses.append(new_course)

            return '200 OK', render('course_list.html', objects_list=site.courses)
        except KeyError:
            return '200 OK', 'No courses have been added yet'


@AddRoute(routes=routes, url='/student-list/')
class StudentListView(ListView):
    template_name = 'student_list.html'

    def get_queryset(self):
        mapper = MapperRegistry.get_current_mapper('student')
        return mapper.all()


@AddRoute(routes=routes, url='/create-student/')
class StudentCreateView(CreateView):
    template_name = 'create_student.html'

    def create_obj(self, data: dict):
        name = data['name']
        name = site.decode_value(name)
        new_obj = site.create_user('student', name)
        site.students.append(new_obj)
        new_obj.mark_new()
        UnitOfWork.get_current().commit()


@AddRoute(routes=routes, url='/add-student/')
class AddStudentByCourseCreateView(CreateView):
    template_name = 'add_student.html'

    def get_context_data(self):
        context = super().get_context_data()
        context['courses'] = site.courses
        context['students'] = site.students
        return context

    def create_obj(self, data: dict):
        course_name = data['course_name']
        course_name = site.decode_value(course_name)
        course = site.get_course(course_name)
        student_name = data['student_name']
        student_name = site.decode_value(student_name)
        student = site.get_student(student_name)
        course.add_student(student)


@AddRoute(routes=routes, url='/api/')
class CourseApi:
    @DebugMethod(name='CourseApi')
    def __call__(self, request):
        return '200 OK', BaseSerializer(site.courses).save()



@AddRoute(routes=routes, url='/contacts/')
class Contacts:
    @DebugMethod(name='Contacts')
    def __call__(self, request):
        return '200 OK', render('contacts.html')


@AddRoute(routes=routes, url='/calendar/')
class Calendar:
    @DebugMethod(name='Calendar')
    def __call__(self, request):
        return '200 OK', render('calendar.html', data=date.today())

@AddRoute(routes=routes, url='/direction/')
class Direction:
    @DebugMethod(name='Direction')
    def __call__(self, request):
        return '200 OK', render('direction.html')


@AddRoute(routes=routes, url='/courses/')
class Courses(ListView):
    template_name = 'courses.html'

    def get_queryset(self):
        mapper = MapperRegistry.get_current_mapper('category')
        return mapper.all()


@AddRoute(routes=routes, url='/create-category/')
class CreateCategory(CreateView):
    template_name = 'create_category.html'

    def create_obj(self, data: dict):
        name = data['name']
        name = site.decode_value(name)
        print(f'cat name={name}')
        new_obj = site.create_category(name, category=name)
        site.categories.append(new_obj)
        new_obj.mark_new()
        UnitOfWork.get_current().commit()

