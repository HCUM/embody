import wx

embody_text = "EMBody: A Data-Centric Toolkit for EMG-Based Interface Prototyping and Experimentation"
aboutText = "Authors: Jakob Karolus, Francisco Kiss, Pawe\u0142 W. Wo\u017Aniak.\n" \
            "Version 1.0 (Aug 2020).\n" \
            "Copyright (c) 2020 LMU Munich. MIT License.\n" \
            "Financially supported by the European Union's Horizon 2020 Programme."

class AboutTab(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)

        self.sizer = wx.BoxSizer(wx.VERTICAL)
        hbox = wx.BoxSizer(wx.HORIZONTAL)
        png_embody = wx.Image("./res/embody.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        bitmap_embody = wx.StaticBitmap(self, -1, png_embody, (0, 0), (png_embody.GetWidth(), png_embody.GetHeight()))
        st_embody = wx.StaticText(self, -1, "EMBody")
        font = wx.Font(60, wx.FONTFAMILY_TELETYPE, wx.NORMAL, wx.BOLD)
        st_embody.SetFont(font)
        hbox.Add(st_embody, flag=wx.ALIGN_CENTER_VERTICAL)
        hbox.Add(bitmap_embody, flag=wx.LEFT, border=60)
        self.sizer.Add(hbox, flag=wx.LEFT | wx.TOP, border=30)

        st_embody_info = wx.StaticText(self, -1, embody_text)
        font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD)
        st_embody_info.SetFont(font)
        self.sizer.Add(st_embody_info, flag=wx.LEFT | wx.TOP, border=30)

        st_info = wx.StaticText(self, -1, aboutText)
        font = wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.FONTWEIGHT_NORMAL)
        st_info.SetFont(font)
        self.sizer.Add(st_info,flag=wx.LEFT | wx.TOP, border=30, proportion=1)

        hbox2 = wx.BoxSizer(wx.HORIZONTAL)
        png_lmu = wx.Image("./res/lmu.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        bitmap_lmu = wx.StaticBitmap(self, -1, png_lmu, (0, 0), (png_lmu.GetWidth(), png_lmu.GetHeight()))
        png_amplify = wx.Image("./res/amplify.png", wx.BITMAP_TYPE_ANY).ConvertToBitmap()
        bitmap_amplify = wx.StaticBitmap(self, -1, png_amplify, (0, 0), (png_amplify.GetWidth(), png_amplify.GetHeight()))
        hbox2.Add(bitmap_lmu)
        hbox2.Add(bitmap_amplify, flag=wx.LEFT, border=50)
        self.sizer.Add(hbox2,flag=wx.LEFT | wx.TOP | wx.BOTTOM, border=30)

        self.SetSizer(self.sizer)
        self.Layout()
