bl_info = {
    "name": "MD2 Import",
    "author": "Paul TOTH",
    "location": "File > Import > Quake2 (.md2)",
    "blender": (2, 80, 0),
    "category": "Import-Export"
}

# register(), unregister(), ...
import bpy

# import bpy.types.Operator
from bpy.types import Operator

# ImportHelper => self.filepath
from bpy_extras.io_utils import ImportHelper 

# filter_glob for ImportHelper
from bpy.props import StringProperty

# struct
import struct
# no need for __init__ with @dataclass
from dataclasses import dataclass

import os

@dataclass
class THeader:
  ident: int
  version: int
  skin_width: int
  skin_height: int
  frame_size: int
  skin_count: int
  vertex_count: int
  uv_count: int
  face_count: int
  glcmd_count: int
  frame_count: int
  skin_ofs: int
  uv_ofs: int
  face_ofs: int
  frame_ofs: int
  glcmd_ofs: int
  end_of_file: int
  
@dataclass
class TTriangle:
  va: int
  vb: int
  vc: int
  ta: int
  tb: int
  tc: int

@dataclass
class TVertex:
  x: int
  y: int
  z: int
  l: int
  
@dataclass
class TVertexInfo:
  mesh: int
  index: int
  
@dataclass
class TMeshInfo:
  mcount: int
  vindex: int
  vinfo: list()
  
@dataclass
class TTexCoord:
  u: int
  v: int
  
@dataclass
class TVector:
  x: float
  y: float
  z: float
  
@dataclass
class TFrame:
  scale: TVector
  trans: TVector
  name: str
  verts: list()
  
@dataclass
class TVertexList:
  verts: list()
  norms: list()
  
md2Normals = [
  [-0.525731,  0.000000,  0.850651], [-0.442863,  0.238856,  0.864188], [-0.295242,  0.000000,  0.955423], 
  [-0.309017,  0.500000,  0.809017], [-0.162460,  0.262866,  0.951056], [ 0.000000,  0.000000,  1.000000], 
  [ 0.000000,  0.850651,  0.525731], [-0.147621,  0.716567,  0.681718], [ 0.147621,  0.716567,  0.681718], 
  [ 0.000000,  0.525731,  0.850651], [ 0.309017,  0.500000,  0.809017], [ 0.525731,  0.000000,  0.850651], 
  [ 0.295242,  0.000000,  0.955423], [ 0.442863,  0.238856,  0.864188], [ 0.162460,  0.262866,  0.951056], 
  [-0.681718,  0.147621,  0.716567], [-0.809017,  0.309017,  0.500000], [-0.587785,  0.425325,  0.688191], 
  [-0.850651,  0.525731,  0.000000], [-0.864188,  0.442863,  0.238856], [-0.716567,  0.681718,  0.147621], 
  [-0.688191,  0.587785,  0.425325], [-0.500000,  0.809017,  0.309017], [-0.238856,  0.864188,  0.442863], 
  [-0.425325,  0.688191,  0.587785], [-0.716567,  0.681718, -0.147621], [-0.500000,  0.809017, -0.309017], 
  [-0.525731,  0.850651,  0.000000], [ 0.000000,  0.850651, -0.525731], [-0.238856,  0.864188, -0.442863], 
  [ 0.000000,  0.955423, -0.295242], [-0.262866,  0.951056, -0.162460], [ 0.000000,  1.000000,  0.000000], 
  [ 0.000000,  0.955423,  0.295242], [-0.262866,  0.951056,  0.162460], [ 0.238856,  0.864188,  0.442863], 
  [ 0.262866,  0.951056,  0.162460], [ 0.500000,  0.809017,  0.309017], [ 0.238856,  0.864188, -0.442863], 
  [ 0.262866,  0.951056, -0.162460], [ 0.500000,  0.809017, -0.309017], [ 0.850651,  0.525731,  0.000000], 
  [ 0.716567,  0.681718,  0.147621], [ 0.716567,  0.681718, -0.147621], [ 0.525731,  0.850651,  0.000000], 
  [ 0.425325,  0.688191,  0.587785], [ 0.864188,  0.442863,  0.238856], [ 0.688191,  0.587785,  0.425325], 
  [ 0.809017,  0.309017,  0.500000], [ 0.681718,  0.147621,  0.716567], [ 0.587785,  0.425325,  0.688191], 
  [ 0.955423,  0.295242,  0.000000], [ 1.000000,  0.000000,  0.000000], [ 0.951056,  0.162460,  0.262866], 
  [ 0.850651, -0.525731,  0.000000], [ 0.955423, -0.295242,  0.000000], [ 0.864188, -0.442863,  0.238856], 
  [ 0.951056, -0.162460,  0.262866], [ 0.809017, -0.309017,  0.500000], [ 0.681718, -0.147621,  0.716567], 
  [ 0.850651,  0.000000,  0.525731], [ 0.864188,  0.442863, -0.238856], [ 0.809017,  0.309017, -0.500000], 
  [ 0.951056,  0.162460, -0.262866], [ 0.525731,  0.000000, -0.850651], [ 0.681718,  0.147621, -0.716567], 
  [ 0.681718, -0.147621, -0.716567], [ 0.850651,  0.000000, -0.525731], [ 0.809017, -0.309017, -0.500000], 
  [ 0.864188, -0.442863, -0.238856], [ 0.951056, -0.162460, -0.262866], [ 0.147621,  0.716567, -0.681718], 
  [ 0.309017,  0.500000, -0.809017], [ 0.425325,  0.688191, -0.587785], [ 0.442863,  0.238856, -0.864188],
  [ 0.587785,  0.425325, -0.688191], [ 0.688191,  0.587785, -0.425325], [-0.147621,  0.716567, -0.681718], 
  [-0.309017,  0.500000, -0.809017], [ 0.000000,  0.525731, -0.850651], [-0.525731,  0.000000, -0.850651], 
  [-0.442863,  0.238856, -0.864188], [-0.295242,  0.000000, -0.955423], [-0.162460,  0.262866, -0.951056], 
  [ 0.000000,  0.000000, -1.000000], [ 0.295242,  0.000000, -0.955423], [ 0.162460,  0.262866, -0.951056], 
  [-0.442863, -0.238856, -0.864188], [-0.309017, -0.500000, -0.809017], [-0.162460, -0.262866, -0.951056], 
  [ 0.000000, -0.850651, -0.525731], [-0.147621, -0.716567, -0.681718], [ 0.147621, -0.716567, -0.681718], 
  [ 0.000000, -0.525731, -0.850651], [ 0.309017, -0.500000, -0.809017], [ 0.442863, -0.238856, -0.864188], 
  [ 0.162460, -0.262866, -0.951056], [ 0.238856, -0.864188, -0.442863], [ 0.500000, -0.809017, -0.309017], 
  [ 0.425325, -0.688191, -0.587785], [ 0.716567, -0.681718, -0.147621], [ 0.688191, -0.587785, -0.425325], 
  [ 0.587785, -0.425325, -0.688191], [ 0.000000, -0.955423, -0.295242], [ 0.000000, -1.000000,  0.000000], 
  [ 0.262866, -0.951056, -0.162460], [ 0.000000, -0.850651,  0.525731], [ 0.000000, -0.955423,  0.295242], 
  [ 0.238856, -0.864188,  0.442863], [ 0.262866, -0.951056,  0.162460], [ 0.500000, -0.809017,  0.309017], 
  [ 0.716567, -0.681718,  0.147621], [ 0.525731, -0.850651,  0.000000], [-0.238856, -0.864188, -0.442863], 
  [-0.500000, -0.809017, -0.309017], [-0.262866, -0.951056, -0.162460], [-0.850651, -0.525731,  0.000000], 
  [-0.716567, -0.681718, -0.147621], [-0.716567, -0.681718,  0.147621], [-0.525731, -0.850651,  0.000000], 
  [-0.500000, -0.809017,  0.309017], [-0.238856, -0.864188,  0.442863], [-0.262866, -0.951056,  0.162460], 
  [-0.864188, -0.442863,  0.238856], [-0.809017, -0.309017,  0.500000], [-0.688191, -0.587785,  0.425325], 
  [-0.681718, -0.147621,  0.716567], [-0.442863, -0.238856,  0.864188], [-0.587785, -0.425325,  0.688191], 
  [-0.309017, -0.500000,  0.809017], [-0.147621, -0.716567,  0.681718], [-0.425325, -0.688191,  0.587785], 
  [-0.162460, -0.262866,  0.951056], [ 0.442863, -0.238856,  0.864188], [ 0.162460, -0.262866,  0.951056], 
  [ 0.309017, -0.500000,  0.809017], [ 0.147621, -0.716567,  0.681718], [ 0.000000, -0.525731,  0.850651], 
  [ 0.425325, -0.688191,  0.587785], [ 0.587785, -0.425325,  0.688191], [ 0.688191, -0.587785,  0.425325], 
  [-0.955423,  0.295242,  0.000000], [-0.951056,  0.162460,  0.262866], [-1.000000,  0.000000,  0.000000], 
  [-0.850651,  0.000000,  0.525731], [-0.955423, -0.295242,  0.000000], [-0.951056, -0.162460,  0.262866], 
  [-0.864188,  0.442863, -0.238856], [-0.951056,  0.162460, -0.262866], [-0.809017,  0.309017, -0.500000], 
  [-0.864188, -0.442863, -0.238856], [-0.951056, -0.162460, -0.262866], [-0.809017, -0.309017, -0.500000], 
  [-0.681718,  0.147621, -0.716567], [-0.681718, -0.147621, -0.716567], [-0.850651,  0.000000, -0.525731], 
  [-0.688191,  0.587785, -0.425325], [-0.587785,  0.425325, -0.688191], [-0.425325,  0.688191, -0.587785], 
  [-0.425325, -0.688191, -0.587785], [-0.587785, -0.425325, -0.688191], [-0.688191, -0.587785, -0.425325]
]
  
class ImportMD2(Operator, ImportHelper):
    """Loads Quake 2 MD2 file"""
    bl_idname = "execute.import_md2"
    bl_label = "Import MD2"
    
    # ImportHelper filter
    filter_glob: StringProperty(
        default="*.md2",
        options={'HIDDEN'}
    )
    
    def get_frame_verts(self, mesh, f, vinfo):
        verts = list()
        for i in range(len(f.verts)):
            for j, vi in enumerate(vinfo):
                if (vi.mesh == mesh) and (vi.index == i):
                    # get the original vertex
                    v = f.verts[j]
                    verts.append([v.x * f.scale.x + f.trans.x, v.y * f.scale.y + f.trans.y, v.z * f.scale.z + f.trans.z])
                    break
        return verts
                
    def get_vert_list(self, mesh, f, vinfo):
        verts = list()
        norms = list()
        # check each possible vertex
        for i in range(len(f.verts)):
            # search for vertex i of the mesh
            for j, vi in enumerate(vinfo):
                if (vi.mesh == mesh) and (vi.index == i):
                    # get the original vertex
                    v = f.verts[j]
                    verts.append([v.x * f.scale.x + f.trans.x, v.y * f.scale.y + f.trans.y, v.z * f.scale.z + f.trans.z])
                    norms.append(md2Normals[v.l])
                    break
        return TVertexList(*[verts, norms]);
    
    def get_faces(self, mesh, triangles, vinfo):
        faces = list()
        for t in triangles:
            if (vinfo[t.va].mesh == mesh):
                faces.append([vinfo[t.va].index, vinfo[t.vb].index, vinfo[t.vc].index])
        return faces
        
    def add_frame(self, col, name, frames, ffirst, flast, fps, triangles, uv, minfo, mat):
        print("add frame ", name)
        parent = bpy.data.collections.new(name)
        col.children.link(parent)
        fcount = (flast - ffirst + 1) * fps # second
        fps = fcount / 24 # convert from MD2 to Blender's 24FPS
        for m in range(minfo.mcount):
            # add mesh
            vlist = self.get_vert_list(m, frames[ffirst], minfo.vinfo)
            faces = self.get_faces(m, triangles, minfo.vinfo)
            mesh = bpy.data.meshes.new(frames[ffirst].name)
            mesh.from_pydata(vlist.verts, [], faces);
            # set normals (don't seems to work !)
            mesh.normals_split_custom_set_from_vertices(vlist.norms)
            mesh.calc_normals_split()
            # add texture mapping
            layer = mesh.uv_layers.new()
            mesh.uv_layers.active = layer
            # layer.data is an array of 3 * face_count of (u,v)            
            i = 0
            for t in triangles:
                if (minfo.vinfo[t.va].mesh == m):
                    layer.data[i].uv = [uv[t.ta].u, uv[t.ta].v]
                    i += 1
                    layer.data[i].uv = [uv[t.tb].u, uv[t.tb].v]
                    i += 1
                    layer.data[i].uv = [uv[t.tc].u, uv[t.tc].v]
                    i += 1
            # add object
            obj = bpy.data.objects.new(frames[ffirst].name, mesh)
            obj.data.materials.append(mat)
            parent.objects.link(obj)
            # animation
            fcount = flast - ffirst
            for i in range(fcount):
                fverts = self.get_frame_verts(m, frames[ffirst + i], minfo.vinfo)
                for idx, v in enumerate(obj.data.vertices):
                    obj.data.vertices[idx].co = fverts[idx]
                    v.keyframe_insert('co', frame = i * fps)
                    # duplicate first animation at the end for interpolation
                    if i == 0: v.keyframe_insert('co', frame = fcount * fps)
        return

    def connect(self, minfo, i, triangles):
        if minfo.vinfo[i].mesh < 0:
            minfo.vinfo[i].mesh = minfo.mcount
            minfo.vinfo[i].index = minfo.vindex
            minfo.vindex += 1
            for t in triangles:
                if (t.va == i):
                    self.connect(minfo, t.vb, triangles)
                    self.connect(minfo, t.vc, triangles)
                if (t.vb == i):
                    self.connect(minfo, t.va, triangles)
                    self.connect(minfo, t.vc, triangles)
                if (t.vc == i):
                    self.connect(minfo, t.va, triangles)
                    self.connect(minfo, t.vb, triangles)
        return
            
                
    def load(self):
        # load file in memory
        with open(self.filepath, "rb") as f:
            md2 = f.read()
        # extract header 17 x Integer, "<" = little-endian
        header = THeader(*struct.unpack("<iiiiiiiiiiiiiiiii", md2[:68]))
        if not header.ident == 844121161:
            print("invalid file format")
            return
        
        # skin names (not used)
        
        # skin_names = list()
        # print("skin count: ", header.skin_count)
        # for x in range(header.skin_count):
        #    o = header.skin_ofs + x * 64
        #    name = md2[o:o + 64].decode("ascii", "ignore")
        #    skin_names.append(name)
        
        # triangles
        triangles = list()
        print("triangles: ", header.face_count)
        for x in range(header.face_count):
            o = header.face_ofs + x * 6 * 2
            triangles.append(TTriangle(*struct.unpack("<hhhhhh", md2[o:o + 6 * 2])))

        # UV
        uv = list()
        print("texcoords: ", header.uv_count)
        for x in range(header.uv_count):
            o = header.uv_ofs + x * 2 * 2
            t = TTexCoord(*struct.unpack("<hh", md2[o:o + 2 * 2]))
            t.u /= header.skin_width
            t.v /= header.skin_height
            uv.append(t)

        # frames
        frames = list()
        print("frames: ", header.frame_count, " of ", header.vertex_count, " vertices")
        for x in range(header.frame_count):
            o = header.frame_ofs + x * header.frame_size
            # scale(x, y, z)
            s = TVector(*struct.unpack("<fff", md2[o:o + 3 * 4]))
            o += 3 * 4
            # trans(x, y, z)
            t = TVector(*struct.unpack("<fff", md2[o:o + 3 * 4]))
            o += 3 * 4
            # name
            n = md2[o:o + 16].decode("ascii", "ignore")
            o += 16
            # vertices
            v = list()
            for i in range(header.vertex_count):
                v.append(TVertex(*struct.unpack("<BBBB", md2[o:o + 4])))
                o += 4
            frames.append(TFrame(s, t, n, v))
        print("file loaded")

        # split meshes
        vinfo = list()
        for v in frames[0].verts:
            vinfo.append(TVertexInfo(*[-1, -1]))
            
        minfo = TMeshInfo(*[0, 0, vinfo])
        for i, vi in enumerate(vinfo):
            if (vi.mesh < 0):
                minfo.vindex = 0
                self.connect(minfo, i, triangles)
                minfo.mcount += 1
                
        print(minfo.mcount, " meshes found")

        # material
        mat = bpy.data.materials.new(name="Material")
        mat.use_nodes = True
        bsdf = mat.node_tree.nodes[0]
        texImage = mat.node_tree.nodes.new('ShaderNodeTexImage')
        mat.node_tree.links.new(bsdf.inputs['Base Color'], texImage.outputs['Color'])
        
        # new collection
        col_name = os.path.split(self.filepath)[-1]
        col = bpy.data.collections.new(col_name)
        bpy.context.scene.collection.children.link(col)
        
        # Animations: http://tfc.duke.free.fr/old/models/md2.htm
        self.add_frame(col, "STAND", frames, 0, 39, 9, triangles, uv, minfo, mat)
        self.add_frame(col, "RUN", frames, 40, 45, 10, triangles, uv, minfo, mat)
        self.add_frame(col, "ATTACK", frames, 46, 53, 10, triangles, uv, minfo, mat)
        self.add_frame(col, "PAIN_A", frames, 54, 57, 7, triangles, uv, minfo, mat)
        self.add_frame(col, "PAIN_B", frames, 58, 61, 7, triangles, uv, minfo, mat)
        self.add_frame(col, "PAIN_C", frames, 62, 65, 7, triangles, uv, minfo, mat)
        self.add_frame(col, "JUMP", frames, 66, 71, 7, triangles, uv, minfo, mat)
        self.add_frame(col, "FLIP", frames, 72, 83, 7, triangles, uv, minfo, mat)
        self.add_frame(col, "SALUTE", frames, 84, 94, 7, triangles, uv, minfo, mat)
        self.add_frame(col, "FALLBACK", frames, 95, 111, 10, triangles, uv, minfo, mat)
        self.add_frame(col, "WAVE", frames, 112, 122, 7, triangles, uv, minfo, mat)
        self.add_frame(col, "POINT", frames, 123, 134, 6, triangles, uv, minfo, mat)
        self.add_frame(col, "CROUCH_STAND", frames, 135, 153, 10, triangles, uv, minfo, mat)
        self.add_frame(col, "CROUCH_WALK", frames, 154, 159, 7, triangles, uv, minfo, mat)
        self.add_frame(col, "CROUCH_ATTACK", frames, 160, 168, 10, triangles, uv, minfo, mat)
        self.add_frame(col, "CROUCH_PAIN", frames, 169, 172, 7, triangles, uv, minfo, mat)
        self.add_frame(col, "CROUCH_DEATH", frames, 173, 177, 5, triangles, uv, minfo, mat)
        self.add_frame(col, "DEATH_FALLBACK", frames, 178, 183, 7, triangles, uv, minfo, mat)
        self.add_frame(col, "DEATH_FALLFORWARD", frames, 184, 189, 7, triangles, uv, minfo, mat)
        self.add_frame(col, "DEATH_FALLBACKSLOW", frames, 190, 197, 7, triangles, uv, minfo, mat)
        self.add_frame(col, "BOOM", frames, 198, 198, 5, triangles, uv, minfo, mat)
        return
    
    def execute(self, context):
        # let's import a file
        print("MD2 Import (c)2023 Paul TOTH")
        print("loading ", self.filepath, "...")
        self.load()
        print("done")
        return {'FINISHED'} 

def menu_func_import(self, context):
    self.layout.operator(ImportMD2.bl_idname, text="Quake 2 Model Import (.md2)")

def register():
    bpy.utils.register_class(ImportMD2)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import)
    
def unregister():
    bpy.utils.unregister_class(ImportMD2)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import)

if __name__ == "__main__":
    register()