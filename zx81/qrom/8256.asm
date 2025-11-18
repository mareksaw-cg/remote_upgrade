  .org	2040h
  xor	a
	ld	hl,2000h
	ld	(hl),a
	ld	de,2001h
	ld	bc,1FFFh
	ldir
	ret
;

	xor	a
	ld	hl,8000h
	ld	(hl),a
	ld	de,8001h
	ld	bc,3FFFh
	ldir
	ld	hl,8066h
	ld	(8000h),hl
	ret
;

	ld	hl,(4014h)
	ld	bc,4009h
	or	a
	sbc	hl,bc
	ld	b,h
	ld	c,l
	ret
;

	call	2161h
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	ret
;

	call	216Eh
	ret
;

	add	hl,bc
	ld	b,b
	or	a
	sbc	hl,bc
	ld	b,h
	ld	c,l
	ld	hl,(2000h)
	sbc	hl,bc
	ld	b,h
	ld	c,l
	ld	hl,(8000h)
	sbc	hl,bc
	ld	b,h
	ld	c,l
	ld	a,(8002h)
	inc	a
	ld	(8002h),a
	ld	(8003h),a
	ld	e,a
	add	a,a
	add	a,e
	ld	e,a
	ld	d,00h
	ld	hl,8004h
	add	hl,de
	ld	a,(8003h)
	ld	(hl),a
	.DB	0EDh,04bh
	nop
	add	a,b
	inc	hl
	ld	(hl),c
	inc	hl
	ld	(hl),b
	ret
;

	call	02E7h
	ld	hl,4009h
	call	20C1h
	call	01FCh
	jr	20B9h

	ld	a,(hl)
	ld	(bc),a
	inc	bc
	ret
;

	call	2062h
	ld	hl,(8000h)
	add	hl,bc
	ld	(8000h),hl
	ret
;

	ld	a,(8003h)
	ld	e,a
	add	a,a
	add	a,e
	ld	e,a
	ld	d,00h
	ld	hl,8004h
	add	hl,de
	inc	hl
	ld	c,(hl)
	inc	hl
	ld	b,(hl)
	ret
;

	call	02E7h
	ld	hl,4009h
	call	20F0h
	call	01FCh
	jr	20E8h

	ld	a,(bc)
	ld	(hl),a
	inc	bc
	ret
;

	call	20D0h
	call	20E2h
	ret
;

	call	2079h
	ld	a,b
	or	c
	ret	z

	call	2092h
	call	20B3h
	call	20C5h
	ret
;

	call	20D0h
	ld	hl,000Bh
	add	hl,bc
	ld	c,(hl)
	inc	hl
	ld	b,(hl)
	ld	de,4009h
	ld	h,b
	ld	l,c
	or	a
	sbc	hl,de
	ld	b,h
	ld	c,l
	ret
;

	ld	hl,2000h
	ld	b,20h
	jr	2133h

	ld	hl,8000h
	inc	bc
	ld	b,b
	jr	2133h

	ld	hl,C000h
	ld	b,40h
	ld	c,00h
	xor	a
	nop
	nop
	nop
	xor	(hl)
	inc	hl
	dec	c
	jr	nz,2139h

	djnz	F9h

	ld	b,00h
	ld	c,a
	ret
;

	ld	a,(2002h)
	out	(7Fh),a
	ret
;

	ld	a,(2002h)
	or	08h
	out	(7Fh),a
	ld	a,(de)
	ld	a,(bc)
	ld	l,00h
	dec	l
	jr	nz,2155h

	dec	h
	jr	nz,2155h

	ld	a,(2002h)
	out	(7Fh),a
	ret
;

	ld	hl,(2000h)
	.DB	0EDh,05bh
	nop
	add	a,b
	or	a
	sbc	hl,de
	ld	b,h
	ld	c,l
	ret
;

	ld	hl,(4014h)
	ld	bc,4009h
	or	a
	sbc	hl,bc
	ld	b,h
	ld	c,l
	ld	hl,(2000h)
	or	a
	sbc	hl,bc
	.DB	0EDh,04bh
	nop
	add	a,b
	or	a
	sbc	hl,bc
	ld	b,h
	ld	c,l
	ret
;

	ld	a,(2002h)
	set	0,a
	ld	(2002h),a
	ld	c,a
	ld	b,00h
	ret
;

	ld	d,d
	ld	b,l
	ld	c,l
	jr	nz,21DDh

	ld	c,a
	ld	d,b
	ld	e,c
	jr	nz,21F2h

	ld	d,h
	ld	b,c
	ld	d,d
	ld	d,h
	dec	l
	ld	a,21h
	add	a,d
	ld	b,b
	ld	de,2000h
	ld	bc,0400h
	ldir
	ret
;

	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	nop
	xor	a
	ld	(hl),a
	ld	d,h
	ld	e,l
	inc	de
	ld	bc,1FFFh
	ldir
	ret
;

	ld	hl,0000h
	ld	de,F000h
	ld	bc,1000h
	ldir
	ret
;

	ld	hl,F000h
	ld	de,0000h
	ld	bc,1000h
	ldir
	ret
;

	ld	hl,8000h
	call	2200h
	ld	hl,C000h
	call	2200h
	ld	hl,C000h
	call	2200h
	ld	hl,E000h
	call	2200h
	ret
;

	ld	hl,8000h
	ld	b,80h
	ld	c,00h
	xor	a
	xor	(hl)
	inc	hl
	dec	c
	jr	nz,2244h

	djnz	F9h

	ld	b,00h
	ld	c,a
	ret
;

	ld	b,05h
	ld	a,(2002h)
	set	4,a
	out	(7Fh),a
	ld	c,00h
	dec	c
	jr	nz,225Ah

	djnz	FBh

	res	4,a
	out	(7Fh),a
	ret
;

	ld	a,(2002h)
	set	0,a
	out	(7Fh),a
	ld	(2002h),a
	ret
;

	ld	a,(2002h)
	res	0,a
	out	(7Fh),a
	ld	(2002h),a
	ret
;

	ld	a,(2002h)
	set	1,a
	out	(7Fh),a
	ld	(2002h),a
	ret
;

	ld	a,(2002h)
	res	1,a
	out	(7Fh),a
	ld	(2002h),a
	ret
;

	call	0F23h
	call	227Ah
	call	224Fh
	call	2217h
	call	224Fh
	call	0F2Bh
	ret
;

	call	0F23h
	call	2285h
	call	0F2Bh
	ret
;

	in	a,(7Fh)
	ld	c,a
	ld	b,00h
	ret
;

	ld	a,(2002h)
	out	(7Fh),a
	ret
;

	ld	hl,2040h
	ld	bc,03C0h
	call	2243h
	ret
;
