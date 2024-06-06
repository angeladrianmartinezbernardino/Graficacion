from time import time
import pygame
from OpenGL.GL import *
from animation import Animation
from sound import Sound


class Model:
    @staticmethod
    def default_draw(ang):
        glLoadIdentity()
        glTranslatef(0, -15, -75)
        glRotatef(-45, 0, 1, 0)
        glRotatef(-90, 1, 0, 0)
        glRotatef(ang, 0, 0, 1)

    def __init__(
            self,
            name,
            assets_folder,
            animations_prefix,
            texture_path,
            initial_position,
            size,
            speed,
            default_sound,
            back,
    ):
        self.name = name
        self.animations = {}
        self.current_animation = None
        self.default_sound = default_sound
        self.current_sound = self.default_sound
        if self.current_sound:
            self.current_sound.start()
        self.texture_path = texture_path
        self.assets_folder = assets_folder
        self.animations_prefix = animations_prefix
        self.default_animation = None
        self.unifTextura = None
        if initial_position:
            self.x = initial_position[0]
            self.y = initial_position[1]
            self.z = initial_position[2]
        else:
            self.x = 0
            self.y = 0
            self.z = 0
        self.rotation = 0
        self.child_models = []
        self.size = size
        self.speed = speed
        self.back = back

    def move_x(self, movement):
        self.x += movement * self.speed

    def move_y(self, movement):
        self.y += movement * self.speed

    def attach_model(self, model):
        self.child_models.append(model)

    def get_models(self):
        return [child.name for child in self.child_models] + [self.name]

    def add_animation(self, animation_type, animation):
        self.animations[animation_type] = animation

    def load_animations(self):
        for prefix in self.animations_prefix:
            sound_info = self.animations_prefix[prefix].get("sound")
            sound = None
            if sound_info:
                sound = Sound(
                    sound_info.get("name"),
                    sound_info.get("volume", 1),
                    sound_info.get("loop", False),
                )
            animation = Animation(prefix, self.animations_prefix[prefix]["frames"], sound, )
            animation.load_animations(self.assets_folder, prefix)
            self.add_animation(prefix, animation)

    def load(self, default_animation, gouraud=None, texture_id=None):
        self.default_animation = default_animation
        self.load_animations()
        if texture_id:
            self.texture = texture_id
        else:
            self.load_texture(f"{self.assets_folder}/{self.texture_path}", gouraud=gouraud)
        self.current_animation = self.animations[self.default_animation]

    def change_animation(self, animation_type=None):
        if self.current_animation and self.current_animation.name == animation_type:
            return
        if not animation_type:
            animation_type = self.default_animation
        self.current_animation = self.animations[animation_type]
        past_sound = self.current_sound
        if past_sound:
            past_sound.stop()
        self.current_sound = (
            self.current_animation.sound if self.current_animation.sound else self.default_sound
        )
        if self.current_sound:
            self.current_sound.start()
        self.current_animation.start_time = time()

    def draw(self, light=False, angle=0):
        Model.default_draw(angle)
        current_obj = self.current_animation.current_obj
        if not self.back:
            glFrontFace(GL_CW)
        else:
            glFrontFace(GL_CCW)
        if self.size:
            glScale(self.size, self.size, self.size)
        glRotatef(self.rotation, 0, 0, 1)
        glTranslate(self.x, self.y, self.z)
        if current_obj.vertexes:
            glEnableClientState(GL_VERTEX_ARRAY)
            glVertexPointer(3, GL_FLOAT, 0, current_obj.vertexes)
        if current_obj.normals:
            glEnableClientState(GL_NORMAL_ARRAY)
            glNormalPointer(GL_FLOAT, 0, current_obj.normals)
        if current_obj.textures:
            glEnableClientState(GL_TEXTURE_COORD_ARRAY)
            glTexCoordPointer(2, GL_FLOAT, 0, current_obj.textures)
            if self.unifTextura is not None:
                try:
                    glUniform1i(self.unifTextura, 0)
                except:
                    print("Error loading unifTexture")
            glBindTexture(GL_TEXTURE_2D, self.texture)
        glDrawArrays(GL_TRIANGLES, 0, len(current_obj.poligons))
        if current_obj.vertexes:
            glDisableClientState(GL_VERTEX_ARRAY)
        if current_obj.normals:
            glDisableClientState(GL_NORMAL_ARRAY)
        if current_obj.textures:
            glBindTexture(GL_TEXTURE_2D, 0)
            glDisableClientState(GL_TEXTURE_COORD_ARRAY)

    def load_texture(self, path, gouraud=None):
        # Cargo la imagen a memoria. pygame se hace cargo de decodificarla correctamente
        surf = pygame.image.load(path)
        # Doy vuelta las texturas
        surf = pygame.transform.flip(surf, False, True)
        # Obtengo la matriz de colores de la imagen en forma de un array binario
        # Le indico el formato en que quiero almacenar los datos (RGBA) y que invierta la matriz, para poder usarla correctamente con OpenGL
        image = pygame.image.tostring(surf, "RGBA", 1)
        # Obentego las dimensiones de la imagen
        ix, iy = surf.get_rect().size
        # Creo una textura vacia en memoria de video, y me quedo con el identificador (texid) para poder referenciarla
        texid = glGenTextures(1)
        # Activo esta nueva textura para poder cargarle informacion
        glBindTexture(GL_TEXTURE_2D, texid)
        # Seteo los tipos de filtro a usar para agrandar y achivar la textura
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_NEAREST)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_NEAREST)
        # Cargo la matriz de colores dentro de la textura
        # Los parametros que le paso son:
        # - Tipo de textura, en este caso GL_TEXTURE_2D
        # - Nivel de mipmap, en este caso 0 porque no estoy usando mas niveles
        # - Formato en que quiero almacenar los datos en memoria de video, GL_RGB en este caso, porque no necesito canal Alfa
        # - Ancho de la textura
        # - Alto de la textura
        # - Grosor en pixels del borde, en este caso 0 porque no quiero agregar borde a al imagen
        # - Formato de los datos de la imagen, en este caso GL_RGBA que es como lo leimos con pygame.image
        # - Formato de los canales de color, GL_UNSIGNED_BYTE quiere decir que son 8bits para cada canal
        # - La imagen, en este caso la matriz de colores que creamos con pygame.image.tostring
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, ix, iy, 0, GL_RGBA, GL_UNSIGNED_BYTE, image)
        # Una vez que tengo todo cargado, desactivo la textura para evitar que se dibuje por error mas adelante
        # Cada vez que quiera usarla, puedo hacer glBindTexture con el identificador (texid) que me guarde al crearla
        glBindTexture(GL_TEXTURE_2D, 0)
        # devuelvo el identificador de la textura para que pueda ser usada mas adelante
        self.texture = texid
        if gouraud:
            self.unifTextura = glGetUniformLocation(gouraud, "textura")
