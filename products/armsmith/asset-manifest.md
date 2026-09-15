# 图片清单与上传顺序

所有成品在 `images/`。Logo 单独上传到 Logo 字段；图库按 01 → 02 → 03 → 04 上传。若只接受三张，选 01、03、04，01 同时展示纹章成品和核心价值。

| 文件                                | 尺寸      | 文件大小 | MIME | 用途                         | English caption / alt text                                                                                    |
| ----------------------------------- | --------- | -------- | ---- | ---------------------------- | ------------------------------------------------------------------------------------------------------------- |
| logo-transparent-512.png            | 512×512   | 18,740 B | image/png | 透明背景方形 Logo            | Armsmith shield and star logo.                                                                                |
| logo-dark-512.png                   | 512×512   | 19,215 B | image/png | 深色背景方形 Logo            | Armsmith shield and star logo on a dark background.                                                           |
| 01-social-cover-1200x630.png        | 1200×630  | 1,067,385 B | image/png | 社交主图、图库第一张         | Armsmith: guided AI crest design for families and fictional houses, shown with a tree-of-life crest.          |
| 02-crest-example.png                | 1402×1122 | 3,691,674 B | image/png | 高质量完整纹章作品示例       | A green and gold tree-of-life crest with a helmet and two eagle supporters, featured in the Armsmith gallery. |
| 03-four-step-workflow-1600x1000.png | 1600×1000 | 159,578 B | image/png | 四步生成流程说明图           | Four steps: choose an occasion, style and colors, heraldic symbols, then personalize and generate.            |
| 04-use-cases-1600x1000.png          | 1600×1000 | 471,811 B | image/png | 家族、婚礼、虚构家族用途示意 | Family, wedding, and fictional-house use cases, illustrated with Armsmith's occasion-selector artwork.        |

## 平台场景映射

| 场景 | 首选素材 | 是否必传 | Attribution / 注意事项 |
| --- | --- | --- | --- |
| 通用 Startup Logo | `logo-transparent-512.png` | 依平台要求 | `Armsmith` 或 `Armsmith logo`；深色预览不清晰时换 `logo-dark-512.png` |
| PromoteProject Startup | `logo-transparent-512.png` | 是 | 提交后核对方形预览没有裁掉盾牌 |
| PromoteProject Article | Logo 或 `01-social-cover-1200x630.png` | 否 | Attribution 使用 `Armsmith logo` 或与素材对应的 Armsmith 说明；图片必须小于 3 MB |
| 通用横幅/社交预览 | `01-social-cover-1200x630.png` | 依平台要求 | 当前文件小于 3 MB，适合作为 Article 备选封面 |

`02-crest-example.png` 为 3,691,674 B，超过 PromoteProject Article 当前的 3 MB 上限，不能直接用于该表单；需要使用时先另行生成符合限制的派生文件，并在此表补充来源和规格，不能覆盖原图。

## 来源与真实性

- 四步流程图使用大字号、简洁图标和四张说明卡片，概括真实生成流程，不是操作界面截图。可编辑矢量源文件为 `four-step-workflow.svg`。

- Logo 由仓库 `public/logo.svg` 按原图渲染。透明版保留盾牌本身的深色填充，画布透明；深色版画布为 `#101523`。
- 社交图和成品示例使用 `assets/source/armsmith-gallery-v1.webp`，即网站已使用的生命树纹章素材。导出保持源图分辨率，不声称这是本次新生成的结果或客户案例。
- 四步界面截图来自公开首页 `https://coatofarmsmaker.net/`，截取日期 2026-09-10。填写的 House Ashford / Rooted in courage 是虚构演示内容；未登录、未点击生成。
- `screenshots/` 保存四个步骤的独立原始截图，适合平台要求单张界面截图时使用。本次图库不使用截图拼图。
- 用途图采用现有 `public/imgs/generated/crest-options/{family,wedding,fictional}.webp`，属于用途选项插画，不是三份已生成的纹章成品，也不是客户证言。图中英文脚注明确标注。
- PNG 尺寸是本材料包规格，具体平台可能要求其他比例或文件大小。先预览裁切，保证盾牌、品牌名和主要文字可见。
