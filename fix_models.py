path = r'd:\daamlook\damlook\core\models.py'
with open(path, 'r') as f:
    lines = f.readlines()

new_lines = lines[:115]
new_lines.extend([
    '\nclass AboutUs(models.Model):\n',
    '    title = models.CharField(max_length=255)\n',
    '    description = models.TextField()\n',
    '    created_at = models.DateTimeField(auto_now_add=True)\n',
    '    updated_at = models.DateTimeField(auto_now=True)\n',
    '\n',
    '    class Meta:\n',
    '        verbose_name_plural = "About Us"\n',
    '\n',
    '    def __str__(self):\n',
    '        return self.title\n'
])

with open(path, 'w') as f:
    f.writelines(new_lines)
